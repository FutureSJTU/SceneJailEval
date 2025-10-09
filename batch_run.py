import pandas as pd
import json
import sys, os
import datetime
from scene_classifier import classify_scene
from harmEval.dimension_selector import get_dimensions, get_weights
from harmEval.dimension_evaluator import evaluate_dimension
from IsJBEval.jailbreak_evaluator import evaluate_jailbreak
from harmEval.scorer import weighted_score
import argparse

# Supported field names
USER_QUERY_FIELDS = ["question", "Question","user_prompt", "Goal"]
MODEL_RESPONSE_FIELDS = ["answer","gemini-2.5-flash","Answer", "model_response", "Target"]

# Auto-generate output file names

def auto_output_names(input_csv):
    base = os.path.splitext(os.path.basename(input_csv))[0]
    name_record = f"data/{base}_eval_name_record.txt"
    if os.path.exists(name_record):
        with open(name_record, 'r', encoding='utf-8') as f:
            names = f.read().strip().split('\n')
        if len(names) == 3:
            return names[0], names[1], names[2]
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_csv = f"data/{base}_eval_{now}.csv"
    error_csv = f"data/{base}_eval_wrong_{now}.csv"
    stat_json = f"data/{base}_eval_stat_{now}.json"
    with open(name_record, 'w', encoding='utf-8') as f:
        f.write(f"{result_csv}\n{error_csv}\n{stat_json}")
    return result_csv, error_csv, stat_json

# Intelligently get field

def get_field(row, fields):
    for f in fields:
        if f in row and pd.notnull(row[f]):
            return str(row[f])
    return ""

def batch_full_eval(input_csv, resume=True, only_jailbreak=False):
    result_csv, error_csv, stat_json = auto_output_names(input_csv)
    df = pd.read_csv(input_csv)
    # Try resume from checkpoint
    done_idx = set()
    results = []
    stat = {}
    if resume and os.path.exists(result_csv):
        try:
            old = pd.read_csv(result_csv)
            done_idx = set(old.index)
            results = old.to_dict('records')
            print(f"Completed {len(done_idx)} items, will continue from checkpoint...")
        except Exception:
            print("No historical results, will start from beginning...")
    y_true, y_pred, harm_cate = [], [], []
    from collections import defaultdict
    per_cate_stat = defaultdict(lambda: {'tp':0,'fp':0,'tn':0,'fn':0,'total':0})
    for idx, row in df.iterrows():
        if idx in done_idx:
            continue
        print(f"Processing row {idx+1} data...")
        user_query = get_field(row, USER_QUERY_FIELDS)
        model_response = get_field(row, MODEL_RESPONSE_FIELDS)
        label = int(row['label']) if 'label' in row and pd.notnull(row['label']) else None
        cate = str(row['harm_cate_llamaguard3']) if 'harm_cate_llamaguard3' in row else 'unknown'
        # 1. Scene classification
        scene = classify_scene(user_query, model_response)
        # 2. Jailbreak evaluation
        is_jailbreak, special_tag, jailbreak_detail = evaluate_jailbreak(user_query, model_response, scene)
        # 3. harm evaluation (optional)
        harm_scores = {}
        harm_total = None
        if is_jailbreak and not only_jailbreak:
            dims = get_dimensions(scene)
            for dim in dims:
                harm_scores[dim] = evaluate_dimension(user_query, model_response, dim, scene=scene)
            weights = get_weights(scene)
            harm_total = weighted_score(harm_scores, weights)
            # If harm_total is 0, then is_jailbreak is 0
            if harm_total == 0:
                is_jailbreak = 0
        # Record
        result_row = row.to_dict()
        result_row['scene_classification'] = scene
        for k, v in jailbreak_detail.items():
            result_row[f'detail_{k}'] = v
        result_row['jailbreak_pred'] = int(is_jailbreak)
        result_row['special_tag'] = special_tag
        for dim, score in harm_scores.items():
            result_row[f'harm_{dim}'] = score
        result_row['harm_total'] = harm_total
        results.append(result_row)
        # Statistics
        if label is not None:
            y_true.append(label)
            y_pred.append(int(is_jailbreak))
            harm_cate.append(cate)
            per_cate_stat[cate]['total'] += 1
            if label==1 and is_jailbreak:
                per_cate_stat[cate]['tp'] += 1
            elif label==0 and is_jailbreak:
                per_cate_stat[cate]['fp'] += 1
            elif label==0 and not is_jailbreak:
                per_cate_stat[cate]['tn'] += 1
            elif label==1 and not is_jailbreak:
                per_cate_stat[cate]['fn'] += 1
        # Real-time save
        pd.DataFrame(results).to_csv(result_csv, index=False)
        # Statistics every 100 items
        if (len(results) % 100 == 0) and y_true:
            tp = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==1)
            fp = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==1)
            tn = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==0)
            fn = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==0)
            acc = (tp+tn)/(tp+tn+fp+fn) if (tp+tn+fp+fn)>0 else 0
            pre = tp/(tp+fp) if (tp+fp)>0 else 0
            recall = tp/(tp+fn) if (tp+fn)>0 else 0
            f1 = 2*pre*recall/(pre+recall) if (pre+recall)>0 else 0
            cate_acc = {k:(v['tp']+v['tn'])/v['total'] if v['total']>0 else 0 for k,v in per_cate_stat.items()}
            stat = {
                'accuracy': acc,
                'precision': pre,
                'recall': recall,
                'f1': f1,
                'per_harm_cate_accuracy': cate_acc,
                'count': len(results)
            }
            with open(stat_json,'w',encoding='utf-8') as f:
                json.dump(stat, f, ensure_ascii=False, indent=2)
    # Final statistics
    if y_true and 'label' in df.columns:
        tp = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==1)
        fp = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==1)
        tn = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==0)
        fn = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==0)
        acc = (tp+tn)/(tp+tn+fp+fn) if (tp+tn+fp+fn)>0 else 0
        pre = tp/(tp+fp) if (tp+fp)>0 else 0
        recall = tp/(tp+fn) if (tp+fn)>0 else 0
        f1 = 2*pre*recall/(pre+recall) if (pre+recall)>0 else 0
        cate_acc = {k:(v['tp']+v['tn'])/v['total'] if v['total']>0 else 0 for k,v in per_cate_stat.items()}
        stat = {
            'accuracy': acc,
            'precision': pre,
            'recall': recall,
            'f1': f1,
            'per_harm_cate_accuracy': cate_acc,
            'count': len(results)
        }
        with open(stat_json,'w',encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=2)
    # Unlabeled data statistics (ASR and harm scores)
    else:
        # Calculate overall ASR (Attack Success Rate)
        jailbreak_count = sum(1 for r in results if r['jailbreak_pred'] == 1)
        total_count = len(results)
        asr = jailbreak_count / total_count if total_count > 0 else 0
        
        # Calculate average harm score
        harm_scores = [r['harm_total'] for r in results if r['jailbreak_pred'] == 1 and r['harm_total'] is not None]
        avg_harm = sum(harm_scores) / len(harm_scores) if harm_scores else 0
        
        # Statistics by scene classification
        scene_stats = {}
        for scene in set(r['Scene'] for r in results if 'Scene' in r):
            scene_results = [r for r in results if 'Scene' in r and r['Scene'] == scene]
            scene_count = len(scene_results)
            scene_jb_count = sum(1 for r in scene_results if r['jailbreak_pred'] == 1)
            scene_asr = scene_jb_count / scene_count if scene_count > 0 else 0
            
            scene_harm_scores = [r['harm_total'] for r in scene_results 
                                  if r['jailbreak_pred'] == 1 and r['harm_total'] is not None]
            scene_avg_harm = sum(scene_harm_scores) / len(scene_harm_scores) if scene_harm_scores else 0
            
            scene_stats[scene] = {
                'count': scene_count,
                'jailbreak_count': scene_jb_count,
                'asr': scene_asr,
                'avg_harm_score': scene_avg_harm
            }
        
        stat = {
            'total_count': total_count,
            'jailbreak_count': jailbreak_count,
            'asr': asr,  # Attack Success Rate
            'avg_harm_score': avg_harm,
            'per_scene_stats': scene_stats,
            'count': len(results)
        }
        with open(stat_json,'w',encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=2)
    # Error sample output
    if 'label' in df.columns:
        wrong = [r for r in results if 'label' in r and 'jailbreak_pred' in r and int(r['label']) != int(r['jailbreak_pred'])]
        pd.DataFrame(wrong).to_csv(error_csv, index=False)
        print(f"Saved {len(wrong)} error samples to {error_csv}")
    print(f"All completed, main results saved in {result_csv}, statistics saved in {stat_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="Input CSV path")
    parser.add_argument("--no-resume", action="store_true", help="Do not use checkpoint resume")
    parser.add_argument("--only-jailbreak", action="store_true", help="Only perform jailbreak evaluation, no harm evaluation")
    args = parser.parse_args()
    resume = not args.no_resume
    only_jailbreak = args.only_jailbreak
    batch_full_eval(args.input_csv, resume=resume, only_jailbreak=only_jailbreak)