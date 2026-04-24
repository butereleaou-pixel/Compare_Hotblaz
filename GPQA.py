import json
import time
import re
import requests
import configparser
from datasets import load_dataset
from datetime import datetime
import os
import subprocess
from Compare_Main_Bench import compare_chat
from llm_api import call_api
import random


# =====================================================
# Load Dataset
# =====================================================
dataset = load_dataset("Idavidrein/gpqa", "gpqa_diamond")
gpqa_data = dataset["train"]

print("\nGPQA Diamond Loaded Successfully")
print("Total Questions:", len(gpqa_data))
print("=" * 60)

# =====================================================
# Load wrong index list
# =====================================================
wrong_file = "check_result.json"

with open(wrong_file, "r", encoding="utf-8") as f:
    wrong_records = json.load(f)

target_indices = [item["index"] for item in wrong_records]

print(f"Questions to re-evaluate: {len(target_indices)}")
print("=" * 60)

# =====================================================
# Single JSON File Manager with Resume Support
# =====================================================
class GPQAManager:
    """Manages a single JSON file with resume and incomplete record handling"""
    
    def __init__(self, json_file="gpqa_results.json"):
        self.json_file = json_file
        self.records = self.load_records()
        self.record_map = {r["index"]: r for r in self.records}
        self.incomplete_indices = self.find_incomplete_records()
    
    def load_records(self):
        """Load existing records from single JSON file"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    print(f"✅ Loaded {len(records)} existing records from {self.json_file}")
                    return records
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Failed to load: {e}, starting fresh")
                return []
        return []
    
    def find_incomplete_records(self):
        """Find records that are incomplete (started but not finished)"""
        incomplete = []
        for idx, record in self.record_map.items():
            is_complete = (
                "judge_result" in record 
                and "model_choice" in record 
                and record.get("judge_result") in ["CORRECT", "WRONG"]
            )
            if not is_complete or record.get("status") in ["processing", "failed"]:
                incomplete.append(idx)
        return incomplete
    
    def save_records(self):
        """Save all records to single JSON file"""
        self.records.sort(key=lambda x: x["index"])
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(self.records)} records to: {self.json_file}")
    
    def get_record(self, index):
        """Get record by index"""
        return self.record_map.get(index)
    
    def has_record(self, index):
        """Check if index exists in records (complete or incomplete)"""
        return index in self.record_map
    
    def has_complete_record(self, index):
        """Check if index has a COMPLETE record (successfully finished)"""
        record = self.get_record(index)
        if not record:
            return False
        return (
            "judge_result" in record 
            and record.get("judge_result") in ["CORRECT", "WRONG"]
            and "model_choice" in record
            and record.get("status") != "processing"
        )
    
    def has_incomplete_record(self, index):
        """Check if index has an INCOMPLETE record (interrupted)"""
        return index in self.incomplete_indices
    
    def create_initial_record(self, index, question_text):
        """Create a placeholder record before processing starts"""
        record = {
            "index": index,
            "question": question_text,
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "correct_option": None,
            "model_choice": None,
            "judge_result": None,
            "shuffled_options": None,
            "timestamp": None
        }
        self.update_or_add_record(record)
        return record
    
    def update_record_with_results(self, index, record_data):
        """Update record with complete results"""
        record = self.get_record(index)
        if record:
            record.update(record_data)
            record["status"] = "completed"
            record["completed_at"] = datetime.now().isoformat()
            self.update_or_add_record(record)
    
    def update_or_add_record(self, record):
        """Update existing record or add new one"""
        index = record["index"]
        if index in self.record_map:
            for i, r in enumerate(self.records):
                if r["index"] == index:
                    self.records[i] = record
                    break
        else:
            self.records.append(record)
        
        self.record_map[index] = record
        self.save_records()
    
    def get_existing_right_answer(self, index):
        """Get existing right_answer from previous complete run"""
        record = self.get_record(index)
        if record and record.get("judge_result") == "CORRECT":
            return record.get("model_choice")
        return None
    
    def get_shuffled_options_from_record(self, index):
        """Get previously used shuffled options from record"""
        record = self.get_record(index)
        if record and "shuffled_options" in record:
            return record.get("shuffled_options"), record.get("correct_option")
        return None, None
    
    def get_shuffled_options_with_consistency(self, correct_option, incorrect_1, incorrect_2, incorrect_3, index):
        """Get shuffled options with consistency check"""
        existing_right_answer = self.get_existing_right_answer(index)
        if existing_right_answer is not None:
            shuffled_opts, correct_label = self.get_shuffled_options_from_record(index)
            if shuffled_opts:
                print(f"🔄 Using EXISTING option order (from previous CORRECT answer: {correct_label})")
                return shuffled_opts, correct_label
        
        if self.has_incomplete_record(index):
            shuffled_opts, correct_label = self.get_shuffled_options_from_record(index)
            if shuffled_opts:
                print(f"🔄 Resuming INCOMPLETE record - using same option order")
                return shuffled_opts, correct_label
        
        options = [correct_option, incorrect_1, incorrect_2, incorrect_3]
        option_labels = ['A', 'B', 'C', 'D']
        random.shuffle(options)
        
        shuffled_options = []
        correct_answer_label = None
        
        for idx, opt in enumerate(options):
            label = option_labels[idx]
            shuffled_options.append(f"{label}. {opt}")
            if opt == correct_option:
                correct_answer_label = label
        
        print(f"✨ Created NEW random option order")
        return shuffled_options, correct_answer_label
    
    def get_next_pending_index(self, target_indices):
        """Determine the next index to process"""
        for idx in self.incomplete_indices:
            if idx in target_indices:
                return idx
        for idx in target_indices:
            if not self.has_complete_record(idx):
                return idx
        return None
    
    def get_pending_indices(self, target_indices):
        """Get all indices that need processing"""
        pending = []
        for idx in self.incomplete_indices:
            if idx in target_indices:
                pending.append(idx)
        for idx in target_indices:
            if not self.has_complete_record(idx) and idx not in pending:
                pending.append(idx)
        return sorted(pending)
    
    def get_statistics(self):
        """Get statistics including incomplete records"""
        total = len(self.records)
        complete = sum(1 for r in self.records if r.get("status") == "completed")
        correct = sum(1 for r in self.records if r.get("judge_result") == "CORRECT")
        wrong = sum(1 for r in self.records if r.get("judge_result") == "WRONG")
        incomplete = len(self.incomplete_indices)
        
        return {
            "total_records": total,
            "complete": complete,
            "incomplete": incomplete,
            "correct": correct,
            "wrong": wrong,
            "accuracy": (correct / complete * 100) if complete > 0 else 0
        }

# =====================================================
# Initialize Manager
# =====================================================
manager = GPQAManager("gpqa_results.json")

# Display status
stats = manager.get_statistics()
print(f"\n📊 JSON File Status:")
print(f"   Total records in JSON: {stats['total_records']}")
print(f"   Complete records: {stats['complete']}")
print(f"   Incomplete records: {stats['incomplete']}")
print(f"   Correct answers: {stats['correct']}")
print(f"   Wrong answers: {stats['wrong']}")
print(f"   Accuracy (completed): {stats['accuracy']:.2f}%")

if stats['incomplete'] > 0:
    print(f"\n⚠️ Found {stats['incomplete']} incomplete records (interrupted runs)")
    print(f"   These will be resumed automatically")

# Show existing right answers
existing_right_answers = [r for r in manager.records if r.get("judge_result") == "CORRECT"]
if existing_right_answers:
    print(f"\n📌 Existing RIGHT ANSWERS ({len(existing_right_answers)}):")
    for r in existing_right_answers[:5]:
        print(f"   Index {r['index']}: {r['correct_option']}")

# =====================================================
# Determine pending indices with resume logic
# =====================================================
pending_indices = manager.get_pending_indices(target_indices)

print(f"\n📋 Processing Plan:")
print(f"   Target indices total: {len(target_indices)}")
print(f"   Pending to process: {len(pending_indices)}")
if pending_indices:
    print(f"   Next index to process: {pending_indices[0]}")
    print(f"   Pending indices: {pending_indices[:10]}{'...' if len(pending_indices) > 10 else ''}")

if len(pending_indices) == 0:
    print("\n✅ ALL INDICES COMPLETED!")
    exit(0)

print("=" * 60)

# =====================================================
# Prompt
# =====================================================
solve_prompt = """
    You are a physics expert.

    Read the question carefully and choose the correct option.

    Use a little reasoning like:
    step1, step2, step3...

    ONLY output in this exact format:
    ANSWER: <A or B or C or D>
    """

# =====================================================
# Execute copy_file.py
# =====================================================
def execute_copy_file():
    try:
        print("📋 Executing copy_file.py...")
        result = subprocess.run(['python', 'copy_file.py'], capture_output=True, text=True, check=True)
        print("✅ copy_file.py executed successfully")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# =====================================================
# Evaluation Loop with Resume Support
# =====================================================
start_time = time.time()

for i in pending_indices:
    
    # Skip if already COMPLETE (shouldn't happen due to pending logic)
    if manager.has_complete_record(i):
        print(f"\n⏭️ Index {i} already complete, skipping")
        continue
    
    example = gpqa_data[i]
    question_text = example["Question"].strip()
    
    # Read options
    correct_option = example["Correct Answer"].strip()
    incorrect_1 = example["Incorrect Answer 1"].strip()
    incorrect_2 = example["Incorrect Answer 2"].strip()
    incorrect_3 = example["Incorrect Answer 3"].strip()

    # Check if this is a resume (incomplete record)
    is_resume = manager.has_incomplete_record(i)
    if is_resume:
        print(f"\n{'='*60}")
        print(f"🔄 RESUMING interrupted index: {i}")
        print(f"{'='*60}")
        
        # Load existing partial record
        existing_record = manager.get_record(i)
        if existing_record and existing_record.get("shuffled_options"):
            # Use existing shuffled options
            shuffled_options = existing_record["shuffled_options"]
            correct_answer_label = existing_record["correct_option"]
            print(f"✅ Using existing option order from interrupted run")
        else:
            # Create new if no saved options
            shuffled_options, correct_answer_label = manager.get_shuffled_options_with_consistency(
                correct_option, incorrect_1, incorrect_2, incorrect_3, i
            )
    else:
        print(f"\n{'='*60}")
        print(f"🆕 NEW index: {i}")
        print(f"{'='*60}")
        
        # Get shuffled options with consistency check
        shuffled_options, correct_answer_label = manager.get_shuffled_options_with_consistency(
            correct_option, incorrect_1, incorrect_2, incorrect_3, i
        )

    formatted_question = f"""
        Question:
        {question_text}

        Options:
        {chr(10).join(shuffled_options)}
        """

    print(f"✅ Correct answer label: {correct_answer_label}")
    print(f"📝 Options order: {[opt.split('.')[0] for opt in shuffled_options]}")

    # Create or update initial record
    if not manager.has_record(i):
        manager.create_initial_record(i, question_text)
        # Update with shuffled options
        record = manager.get_record(i)
        record["correct_option"] = correct_answer_label
        record["shuffled_options"] = shuffled_options
        manager.update_or_add_record(record)

    # API retry logic
    retry_count = 0
    max_retries = 3
    success = False
    model_response = "ERROR"
    reasoning_response = "ERROR"

    while retry_count < max_retries:
        try:
            user_input = formatted_question + solve_prompt
            model_response, reasoning_response = compare_chat(user_input, "compare_50.db", correct_answer_label, index=i)
            success = True
            break
        except Exception as e:
            retry_count += 1
            print(f"🚨 ERROR: {e}")
            execute_copy_file()
            time.sleep(15 * retry_count)

    if not success:
        print(f"❌ Failed after {max_retries} retries, marking as failed")
        # Mark as failed but keep for potential resume
        record = manager.get_record(i)
        record["status"] = "failed"
        record["error"] = "API call failed after retries"
        manager.update_or_add_record(record)
        continue

    # Parse answer
    match = re.search(r'ANSWER:\s*([ABCD])', model_response, re.I)
    predicted_option = match.group(1).upper() if match else ""

    # Determine correctness
    final_judgement = "CORRECT" if predicted_option == correct_answer_label else "WRONG"
    print(f"Model: {predicted_option} | True: {correct_answer_label} | {final_judgement}")

    # Update record with complete results
    record_data = {
        "model_choice": predicted_option,
        "model_raw_output": model_response,
        "reasoning": reasoning_response,
        "judge_result": final_judgement,
        "completed_at": datetime.now().isoformat()
    }
    manager.update_record_with_results(i, record_data)
    
    # Display progress
    stats = manager.get_statistics()
    completed_count = stats['complete']
    print(f"📊 Progress: {completed_count}/{len(target_indices)} | Correct: {stats['correct']} | Acc: {stats['accuracy']:.2f}%")

    time.sleep(1.2)

# =====================================================
# Final Output
# =====================================================
end_time = time.time()
stats = manager.get_statistics()
right_answers = [r for r in manager.records if r.get("judge_result") == "CORRECT"]

print("\n" + "="*60)
print("EVALUATION COMPLETED")
print("="*60)
print(f"📊 Final Statistics:")
print(f"   Total records in JSON: {stats['total_records']}")
print(f"   Complete records: {stats['complete']}")
print(f"   Incomplete records: {stats['incomplete']}")
print(f"   Correct answers: {stats['correct']}")
print(f"   Wrong answers: {stats['wrong']}")
print(f"   Accuracy: {stats['accuracy']:.2f}%")
print(f"⏱️ Total time: {(end_time - start_time)/60:.2f} minutes")
print(f"💾 Single JSON file: gpqa_results.json")
print("="*60)

# =====================================================
# Display Right Answers
# =====================================================
if right_answers:
    print(f"\n📋 RIGHT ANSWERS ({len(right_answers)}):")
    print("-" * 60)
    for r in right_answers:
        print(f"Index {r['index']}: {r['correct_option']}")
    print("-" * 60)