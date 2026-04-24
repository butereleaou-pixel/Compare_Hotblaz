import json
import time

def monitor_gpqa_results(file_path, check_interval=30):
    # Initialize previous counts
    prev_wrong = -1
    prev_correct = -1
    
    while True:
        try:
            # Read and parse JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Count wrong and correct answers
            current_wrong = 0
            current_correct = 0
            
            for entry in data:
                judge_result = entry.get('judge_result', '')
                if judge_result == 'CORRECT':
                    current_correct += 1
                else:
                    current_wrong += 1
            
            # Print only if counts have changed
            if current_wrong != prev_wrong or current_correct != prev_correct:
                sum_n = current_wrong + current_correct
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Wrong Answers: {current_wrong} | Run Questions: {sum_n} ")
                prev_wrong = current_wrong
                prev_correct = current_correct
            
            # Wait before next check
            time.sleep(check_interval)
            
        except FileNotFoundError:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: File '{file_path}' not found. Retrying...")
            time.sleep(check_interval)
        except json.JSONDecodeError:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: Invalid JSON format. Retrying...")
            time.sleep(check_interval)
        except KeyboardInterrupt:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring stopped by user.")
            break

# Example usage:
file_path = 'gpqa_checkpoint.json'
monitor_gpqa_results(file_path, check_interval=30)  # Check every 30 seconds
