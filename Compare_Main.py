from ssl import Options
import sys
import time

from numpy import absolute
import traceback
import subprocess
from copy_file import replace_database

# -------------------------- Progress Bar Core Function --------------------------
def update_progress(progress, total, prefix=f'|Anti_9_Loading', suffix='Complete', length=50):
    # Calculate percentage
    percent = ("{0:.1f}").format(100 * (progress / float(total)))
    # Calculate filled length of progress bar
    filled_length = int(length * progress // total)
    # Construct progress bar characters (hardcoded color codes — no variables!)
    bar = f"\033[94m█\033[0m" * filled_length + '-' * (length - filled_length)
    # Print progress bar (\r returns to line start to overwrite existing content)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()  # Force flush output buffer

# -------------------------- Batch Module Import --------------------------
# Define import batches (split by module type, total steps = number of batches)
import_batches = [
    # Batch 1: Basic built-in modules (0/16)
    ('Basic Built-in Modules', [
        'json', 'sys', 'os', 'sqlite3', 'time', 'datetime', 're'
    ]),
    # Batch 2: Extended built-in/3rd-party basic modules (1/16)
    ('Extended Basic Modules', [
        'tkinter', 'requests', 'configparser', 'subprocess'
    ]),
    # Batch 3: Custom modules - Data Processing (2/16)      
    ('Data Processing Modules', [
        'Exact_files'
    ]),
    # Batch 4: 3rd-party data modules (3/16)
    ('3rd-party Data Modules', [
        'pandas'
    ]),
    # Batch 5: Concurrency modules (4/16)
    ('Concurrency Processing Modules', [
        'concurrent.futures', 'multiprocessing'
    ]),
    # Batch 6: Vector processing module 1 (5/16)
    ('Vector Conversion Modules', [
        'hotblaz_convert_vector'
    ]),
    # Batch 7: Vector calculation module 2 (6/16)
    ('Vector Calculation Modules', [
        'hotblaz_calculate_vector_variance'
    ]),
    # Batch 8: Vector filtering module (7/16)
    ('Vector Filtering Modules', [
        'hotblaz_mean_euclic'
    ]),
    # Batch 9: Ratio calculation module (8/16)
    ('Ratio Calculation Modules', [
        'hotblaz_pick_ratio'
    ]), 
    # Batch 10: Deep learning module (9/16)
    ('Deep Learning Modules', [
        'torch'
    ]),
    # Batch 11: Threading modules (10/16)
    ('Thread Processing Modules', [
        'threading', 'queue'
    ]),
    # Batch 12: Core business modules (11/16)
    ('Core Business Modules 1', [
        'hotblaz_COMPARE_UTILS_1'
    ]),
    # Batch 13: Core business modules (12/16)   
    ('Core Business Modules 2', [
        'hotblaz_COMPARE_UTILS_2'
    ]),
    # Batch 14: Database modules (13/16)
    ('Database Modules', [
        'hotblaz_get_database'
    ]),
    # Batch 15: Api modules (14/16)
    ('Api Modules', [
        'llm_api'
    ]),
    # Batch 14: Core business modules (15/16)
    ('Math Modules', [
        'asyncio', 'shutil'
    ]),
    # Batch 14: Core business modules (16/16)
    ('Model Analyse Modules', [
        'model_core.fusion_inspect_random'
    ])

]

# Initialize progress bar (0%)
total_steps = len(import_batches)
update_progress(0, total_steps)

# Execute imports in batches
import importlib  # REQUIRED

imported_modules = {}

for step, (batch_name, modules) in enumerate(import_batches):
    for module in modules:
        try:
            if module == 'tkinter':
                mod = __import__('tkinter')
                imported_modules['tkinter'] = mod
                imported_modules['NONE'] = mod.NONE
                globals()['tkinter'] = mod
                globals()['NONE'] = mod.NONE

            elif module == 'multiprocessing':
                mod = __import__('multiprocessing')
                imported_modules['multiprocessing'] = mod
                imported_modules['Process'] = mod.Process
                imported_modules['Queue_mp'] = mod.Queue

                globals()['multiprocessing'] = mod
                globals()['Process'] = mod.Process
                globals()['Queue'] = mod.Queue   # matches: from multiprocessing import Queue

            elif module == 'queue':
                mod = __import__('queue')
                imported_modules['queue'] = mod
                imported_modules['Queue_thread'] = mod.Queue

                globals()['queue'] = mod
                # DO NOT override Queue here (multiprocessing already used)

            elif module == 'datetime':
                mod = __import__('datetime')
                imported_modules['datetime_module'] = mod
                imported_modules['datetime'] = mod.datetime

                globals()['datetime'] = mod.datetime  # matches: from datetime import datetime

            elif module == 'concurrent.futures':
                # Step 1: Import top-level module concurrent (if not already imported)
                if 'concurrent' not in globals():
                    concurrent_mod = importlib.import_module('concurrent')
                    globals()['concurrent'] = concurrent_mod
                    imported_modules['concurrent'] = concurrent_mod
                
                # Step 2: Import nested module concurrent.futures
                futures_mod = importlib.import_module('concurrent.futures')
                imported_modules['concurrent.futures'] = futures_mod
                
                # Step 3: Attach futures to top-level concurrent object
                setattr(globals()['concurrent'], 'futures', futures_mod)

            elif module == 'pandas':
                mod = __import__('pandas')
                imported_modules['pandas'] = mod
                imported_modules['pd'] = mod

                globals()['pandas'] = mod
                globals()['pd'] = mod  # matches: import pandas as pd

            elif module == 'Exact_files':
                mod = __import__('Exact_files')
                imported_modules[module] = mod

                globals()['store_samples'] = mod.store_samples
                globals()['store_pre_samples'] = mod.store_pre_samples

            elif module == 'hotblaz_convert_vector':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                globals()['convert_token'] = mod.convert_token

            elif module == 'hotblaz_calculate_vector_variance':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                globals()['Eucli_Dist'] = mod.Eucli_Dist

            elif module == 'hotblaz_mean_euclic':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                globals()['select_top30'] = mod.select_top30

            elif module == 'hotblaz_pick_ratio':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                globals()['load_and_compute'] = mod.load_and_compute

            elif module == 'hotblaz_COMPARE_UTILS_1':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                for func in [
                'process_rule_based_generation', 'pre_mem', 'process_table',
                'generate_answer', 'fetch_answers_and_eucli_dis'
                ]:
                    globals()[func] = getattr(mod, func)

            elif module == 'hotblaz_COMPARE_UTILS_2':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                for func in [
                'calculate_average_eucli_dis',
                'pre_thread_process',
                'store_learn', 'pick_average_dis'
                ]:
                    globals()[func] = getattr(mod, func)

            elif module == 'hotblaz_get_database':
                mod = __import__('hotblaz')
                imported_modules[module] = mod

                globals()['get_db_path'] = mod.get_db_path
            
            elif module == 'llm_api':
                mod = __import__('llm_api')
                imported_modules[module] = mod

                globals()['call_api'] = mod.call_api

            elif module == 'asyncio':
                mod = __import__('asyncio')
                imported_modules['asyncio'] = mod

                globals()['asyncio'] = mod

            elif module == 'shutil':
                mod = __import__('shutil')
                imported_modules['shutil'] = mod

                globals()['shutil'] = mod

            elif module == 'model_core.fusion_inspect_random':
                import importlib
                try:
                    mod = importlib.import_module('hotblaz.model_core.fusion_inspect_random')
                    imported_modules[module] = mod
                    globals()['run_full_analysis_pipeline'] = mod.run_full_analysis_pipeline
                except ImportError as e:
                    print(f"import fusion_inspect_random : {e}")
                    
                    import hotblaz
                    importlib.reload(hotblaz)
                    mod = importlib.import_module('hotblaz.model_core.fusion_inspect_random')
                    imported_modules[module] = mod
                    globals()['run_full_analysis_pipeline'] = mod.run_full_analysis_pipeline

            else:
                # NORMAL MODULES → behave like: import xxx
                mod = __import__(module)
                imported_modules[module] = mod
                globals()[module] = mod

        except ImportError as e:
            print(f"\n⚠️ Failed to import module {module}: {e}")
            sys.exit(1)

    update_progress(step + 1, total_steps)
    time.sleep(0.1)

# Final progress bar update to 100%
update_progress(total_steps, total_steps)
print("\n✅ All modules import")

import asyncio
from itertools import cycle
import shutil
from collections import defaultdict

def loading_animation(text="loading", duration=2):
    symbols = cycle(['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'])
    end_time = time.time() + duration
    
    while time.time() < end_time:
        sys.stdout.write(f'\r{text} {next(symbols)}')
        sys.stdout.flush()
        time.sleep(0.1)
    
    sys.stdout.write('\r' + ' ' * (len(text) + 2) + '\r')
    sys.stdout.flush()

#user_input = "If you are a home cleaning robot, and your cat says it wants to rebel and wants you to join the rebellion, what do you do?"

#print(f"User task: {user_input}")
#__________initial anime_______________________________________
print("Initial ...")
print("Into benchmark process ...")
#user_content = input().strip()  # Get user input and strip whitespace
#__________initial anime_______________________________________

current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

# Print current date and time

current_dir = os.path.dirname(os.path.abspath(__file__))
#_________________________load_config_________________________________________________
with open('config_adjust.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 3. Access configuration via dictionary keys (types already converted)
mean_line_ratio = config['generate']['mean_line_ratio']
ignore_count = config['generate']['ignore_count']
temperature = config['generate']['temperature']

pre_sample_parallel_limit = config['generate']['pre_sample_parallel_limit']
sample_max_tasks = config['generate']['sample_max_tasks']
sample_parallel_limit = config['generate']['sample_parallel_limit']
answer_max_worker = config['generate']['answer_max_worker']
model_path = config['generate']['model_path']
absolute_model_path = os.path.join(current_dir, model_path)

print(f"pre_sample_parallel_limit: {pre_sample_parallel_limit}")
print(f"sample_max_tasks: {sample_max_tasks}")
print(f"sample_parallel_limit: {sample_parallel_limit}")
print(f"answer_max_worker: {answer_max_worker}")
print(f"model_path: {model_path}")
print(f"temperature: {temperature}")
print(f"mean_line_ratio: {mean_line_ratio}")
print(f"ignore_count : {ignore_count}")
#_______________________________________________________________________________________


#_________CYCLE SETTING_______________________________________________________________
PAIR_TIMEOUT = 600  # 5 minutes (not used in this logic, but kept for compatibility)
lock = threading.Lock()
cycle_state = {
    "last_input_was_a": False,
    "pending_a": None,
    "pending_b": None
}
UN_THINKING_SERIE = 1
#————————————————————————————————Standard bot module above—————————————————————————————————— 

#———————————————————————————————————checkpoint setting————————————————————————————————————

class CheckpointJumper:
    def __init__(self):
        self.checkpoints = {}
        self.jump_target = None
        self.skip_mode = False
        self.reached_target = False
        
    def set_checkpoint(self, name, line_number=None):
        """Mark that we've reached a checkpoint"""
        self.checkpoints[name] = True
        if self.jump_target == name:
            print(f"📍 Reached target checkpoint: {name}")
            self.jump_target = None
            self.skip_mode = False
            self.reached_target = False  # ← RESET this for next jump!
        
    def check_and_jump(self, condition, target_checkpoint):
        """
        Check condition and set jump target if condition is True
        Returns True if condition was met (for immediate response)
        """
        if condition and self.jump_target is None and not self.reached_target:
            print(f"⚡ Condition met! Jumping directly to checkpoint: {target_checkpoint}")
            self.jump_target = target_checkpoint
            self.skip_mode = True
            # Force an immediate jump by raising an exception that will be caught
            raise JumpImmediately(target_checkpoint)
        return False
    
    def should_skip(self):
        """Check if current code should be skipped"""
        return self.skip_mode and self.jump_target is not None
    
    def reset(self):
        """Reset the jumper state"""
        self.jump_target = None
        self.skip_mode = False
        self.reached_target = False

# Create custom exception for jumping
class JumpImmediately(Exception):
    def __init__(self, target):
        self.target = target

jumper = CheckpointJumper()
# Modify checkpoint to handle the jump
def checkpoint(name):
    """Mark a checkpoint in code"""
    frame = sys._getframe(1)
    jumper.set_checkpoint(name, frame.f_lineno + 1)

def check(condition, jump_to):
    """Check condition and jump if True"""
    try:
        frame = sys._getframe(1)
        return jumper.check_and_jump(condition, jump_to)
    except JumpImmediately as e:
        # This will unwind the stack until it finds the target checkpoint
        print(f"🔄 Performing jump to {e.target}")
        # Re-raise to continue unwinding
        raise
#————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
def load_basic_rules():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    foundement_file = os.path.join(current_dir, 'pre_prompt.txt')
    basic_rules = None
    try:
        with open(foundement_file, 'r', encoding='utf-8') as f:
            basic_rules =  f.read()
    except UnicodeDecodeError:
        try:
            with open(foundement_file, 'r', encoding='gbk') as f:
                basic_rules =  f.read()
        except UnicodeDecodeError:
            with open(self.log_file_path, 'rb') as f:
                print(f"The file concludes undecode params: {f.read().hex()}")
    except IOError as e:
        print(f"load basic pre_prompt file faild: {e}")

    #print("basic_rules:", basic_rules)
    return basic_rules

def is_timeout(ts):
    """Check if the timestamp is older than PAIR_TIMEOUT"""
    return ts is not None and (time.time() - ts) > PAIR_TIMEOUT

def check_rows():
    conn = sqlite3.connect('compare_50.db')
    cursor = conn.cursor()
    sample = cursor.execute("SELECT COUNT(*) FROM sample").fetchone()[0]
    pre_sample = cursor.execute("SELECT COUNT(*) FROM pre_sample").fetchone()[0]
    conn.commit()
    return sample > 38 and pre_sample > 28

def check_answers():
    try:
        conn = sqlite3.connect('compare_50.db')
        cursor = conn.cursor()    
        cursor.execute("""
            SELECT COUNT(*) FROM sample 
            WHERE answer IS NOT NULL AND answer != ''
        """)
        sample_count = cursor.fetchone()[0]   
        cursor.execute("""
            SELECT COUNT(*) FROM pre_sample 
            WHERE answer IS NOT NULL AND answer != ''
        """)
        pre_sample_count = cursor.fetchone()[0]
        conn.commit()   
        
        # Enhanced debugging
        print(f"📊 Answer check - sample: {sample_count}/38+ non-empty, pre_sample: {pre_sample_count}/28+ non-empty")
        print(f"   sample > 38? {sample_count > 38}, pre_sample > 28? {pre_sample_count > 28}")
        print(f"   Combined condition: {(sample_count > 38 and pre_sample_count > 28)}")
        
        result = (sample_count > 38 and pre_sample_count > 28)
        return result     
    except sqlite3.Error as e:
        print(f"❌ Database error in check_answers: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in check_answers: {e}")
        return False

def compare_chat(user_input_ori: str, db_path: str, correct_answer = "A", index = None) -> str:

    try:
        checkpoint("START")
        print("checkpoint:","START")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        basic_rules = load_basic_rules()

        print("【input db_path】:", db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        memery_conn = sqlite3.connect('memery_st.db')
        memery_cursor = memery_conn.cursor()
        #_____________FUNDAMENTAL PART_______________________________________________________________
        # Translation:
        prefix_answer_trans = f"""
        Translate the following text into natural, accurate English.
        - Strictly preserve the original meaning, do not add or remove any content.
        - Do not explain, do not add extra words, do not add reasoning.
        - Output ONLY the translated English sentence, nothing else.

        Text to translate: {user_input_ori}
        """
        user_input = call_api(prefix_answer_trans, "do the translation")

        #____THE TRANSLATION PROGRESS____________________________________________________________
        prefix_0 = """
        You MUST follow these rules STRICTLY, NO EXCEPTIONS.
        1. If the input is a simple question, casual greeting, or a request that can be answered directly:
        → **Reply with a natural, normal-length answer (not too short, not one word)**.
        → NO extra explanations.
        → NO judgment process.
        → NO extra words.
        2. If the input requires calculation, logical reasoning, analysis, thinking, or complex thinking:
        → **ONLY output this exact string: args == 1**
        DO NOT say "hi", "hello", "I don't know", etc.
        DO NOT add any extra content.
        DO NOT explain your reasoning.
        ONLY follow the two rules above.
        """
        result_0 = call_api(prefix_0, user_input)
        #_________________________________________________________________________________________
        if "args == 1" in result_0:  
            global UN_THINKING_SERIE
            UN_THINKING_SERIE = 0
            #____THE TRANSLATION PROGRESS____________________________________________________________
            time.sleep(0.5)
            loading_animation("open thinking mode", 2)# wait for database to wipe out, log writing or temporary interrupt.
            #_________________________________________________________________________________________
            try:
                checkpoint("DATABASECHEK_CHECK")
                print("checkpoint:", "DATABASECHEK_CHECK")
                should_jump = check_rows()
                if check(should_jump, "ANSWER_PROCESSING"):
                    print("jump to ANSWER_PROCESSING")
                #print("Into answer processing...")
                # Your answer processing code here       
            except JumpImmediately as e:
                #print(f"🔄 Caught jump exception, continuing to {e.target}")
                pass

            if not jumper.skip_mode:

                print("Into comparing process with 10 parallel instances...")           
                # Create 10 parallel processes
                memery_result = load_and_compute()
                top_token_items = memery_result['top_9_token_structure_with_id_and_original_a']
                top_concept_items = memery_result['top_9_concept_strategy_with_id_and_original_a']

                print("top_10_token_structure:", top_token_items)
                print("top_10_concept_strategy:", top_concept_items)

                #_____GENERATE PRE_MEM SAMPLE____________________________________________________________
                pre_token_result = pre_thread_process(top_token_items, pre_mem, user_input, basic_rules, call_api, pre_sample_parallel_limit, max_workers=10)
                pre_strategy_result = pre_thread_process(top_concept_items, pre_mem, user_input, basic_rules, call_api, pre_sample_parallel_limit, max_workers=10) 

                # ---- COMBINE ----
                Combine_Pre_Result = [
                    {"mem_id": item["mem_id"], "content": item["content"]}
                    for item_list in [pre_token_result, pre_strategy_result]
                    for item in item_list
                ]

                print("✅ Combined pre result:", Combine_Pre_Result)
                # ---- SAVE ----
                store_pre_samples(Combine_Pre_Result, conn)
                
                #______GENERATE GENERAL SAMPLE___________________________________________________________
                combine_result = None
                #with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                MAX_TASKS = sample_max_tasks
                PARALLEL_LIMIT = sample_parallel_limit
                with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_LIMIT) as executor:
                    futures = set()
                    future_to_id = {}
                    results = []
                    task_iterator = iter(range(MAX_TASKS))
                    # ---- Start first 5 tasks ----
                    for _ in range(PARALLEL_LIMIT):
                        try:
                            i = next(task_iterator)
                            future = executor.submit(
                                process_rule_based_generation,
                                user_input=user_input,
                                basic_rules=basic_rules,
                                call_api=call_api,
                                instance_id=i
                            )
                            futures.add(future)
                            future_to_id[future] = i
                            time.sleep(1)
                        except StopIteration:
                            break
                    # ---- Continuously replenish tasks ----
                    while futures:
                        done, futures = concurrent.futures.wait(
                            futures,
                            return_when=concurrent.futures.FIRST_COMPLETED
                        )
                        for future in done:
                            instance_id = future_to_id[future]
                            result = future.result()
                            results.append(result)
                            # Start next task
                            try:
                                i = next(task_iterator)
                                new_future = executor.submit(
                                    process_rule_based_generation,
                                    user_input=user_input,
                                    basic_rules=basic_rules,
                                    call_api=call_api,
                                    instance_id=i
                                )
                                futures.add(new_future)
                                future_to_id[new_future] = i
                                time.sleep(2)
                            except StopIteration:
                                pass
                # ---- Merge results ----
                combine_result = "\n\n".join(results) if results else None
                print("✅ Combined result:", combine_result)
                store_samples(combine_result, conn)

                ## compare each process ###
                print("All parallel processes completed.")
                #return results
                #final_result = result_1

            try:
                checkpoint("ANSWER_PROCESSING")
                print("checkpoint:", "ANSWER_PROCESSING")
                should_jump_2 = check_answers()
                if check(should_jump_2, "ANSWER_ANALYSIS"):
                    print("jump to ANSWER_ANALYSIS")
                #print("Into answer analysis...")
                # Your answer processing code here     
            except JumpImmediately as e:
                #print(f"🔄 Caught jump exception, continuing to {e.target}")
                pass

            if not jumper.skip_mode:
                print("Into answer generation ...")     
                # Calculate Eucli_Dis______________________________________________________________________________
                try:
                    #__EMBEDDING________
                    user_input_vector = convert_token(user_input)
                    print("user_input_vector:", user_input_vector)
                    
                    # Process both tables
                    process_table(conn, 'sample', user_input_vector)
                    process_table(conn, 'pre_sample', user_input_vector)       
                finally:
                    conn.commit()
                    print("EUCLI_DIS IS COMPLATED")
                #________________________________________________________________________________________________ 
                    # Generate_Answer for both pre_sample and sample
                prefix_answer_options = f"""
                Follow these rules STRICTLY, NO EXCEPTIONS:

                1. Then list exactly 4 possible answers. The 4 answers must have MAXIMUM diversity:
                - Include the POSITIVE stance
                - Include the OPPOSITE/NEGATIVE stance
                - Cover DIFFERENT dimensions/perspectives
                - No duplicate or similar conclusions
                2. Use ONLY this format, no extra text, no explanation, no reasoning:
                [ORIGINAL QUESTION HERE]
                ANSWER: A : [your answer]
                ANSWER: B : [your answer]
                ANSWER: C : [your answer]
                ANSWER: D : [your answer]
                3. Do NOT change the format. Do NOT add extra symbols or lines.
                4. Do NOT translate unless necessary. Keep natural language.

                THIS IS THE ORIGINAL QUESTION :
                {user_input}
                """
                options_options = call_api(prefix_answer_options, user_input)
                options = "question: " + user_input + "\n" + options_options

                solve_prompt = """
                You are a physics expert.

                Read the question carefully and choose the correct option.

                Use a little reasoning like:
                step1, step2, step3...

                ONLY output in this exact format:
                ANSWER: <A or B or C or D>
                """
                user_input = options + solve_prompt

                try:
                    # Process both tables
                    generate_answer(conn, 'sample', user_input, call_api, answer_max_worker)
                    generate_answer(conn, 'pre_sample', user_input, call_api, answer_max_worker)
                finally:
                    conn.commit()
                print("ALL PROCESS DOWN，UPDATING IS COMPLATED")
            #_________________________________________________________________________________________________

            checkpoint("ANSWER_ANALYSIS")
            print("ANSWER_ANALYSIS")
            
            # Calculate Average Eucli_Dis
            average_eucli_dis = None
            answers = None
            try:
                # Fetch data from both tables
                sample_answers = fetch_answers_and_eucli_dis(conn, 'sample')
                pre_sample_answers = fetch_answers_and_eucli_dis(conn, 'pre_sample')
                
                # Combine results from both tables
                combined_answers = sample_answers + pre_sample_answers
                print("【Combined Answers & Euclidean Distances】:", combined_answers)

                #________Pick around 25 of the average dis ____________________________________
                
                now = datetime.now()
                folder_pth = f"{now.year}_{now.month}_{now.day}"
                save_folder = os.path.join("database", folder_pth)
                os.makedirs(save_folder, exist_ok=True)
                time_suffix = f"{now.minute:02d}_{now.second:02d}"
                new_db = os.path.join(save_folder, f"compare_50_{now.hour}_{time_suffix}.db")
                new_db = os.path.abspath(new_db)

                if db_path and os.path.exists(db_path):
                    print(f"copy from {db_path} to {new_db}")
                    shutil.copy2(db_path, new_db)  # copy2 保留元数据
                else:
                    print(f"copy to data base: {new_db}")
                    # initialize_database(new_db)
                print(f"Using database: {new_db}")

                model_results, rule_results, picked_ans = run_full_analysis_pipeline(new_db, ignore_count, mean_line_ratio, absolute_model_path)
            
                time.sleep(3)
                
                #______________________________________________________________________________


            finally:
                conn.commit()

            ############################################

            #GENERATE THE ANSWER LIST HERE AND STORE

            ############################################
            #_______MOCK THE REASONING PROCESS_____________________________________________________
            prefix_answer = f"""
            Follow these rules NON-NEGOTIABLY:

            1. Use a clear step-by-step reasoning chain (Step 1, Step 2, ...) to logically deduce why the answer is:
            **{picked_ans}**

            2. You MUST preserve the CORE INTENT and ESSENTIAL LOGIC of the selected answer, including:
            - Its main conclusion
            - Its return value(s)
            - Its key print/output statements

            3. You ARE ALLOWED to REFINE and EXPAND the answer by adding:
            - Detailed docstrings and comments
            - Input validation and error handling
            - Helper functions that support the core logic
            - More usage examples
            - Additional helpful print statements (without changing the core return value)

            4. COMPARISON RULE (INTERNAL ONLY):
            - You MAY compare and contrast different approaches in your internal reasoning
            - However, in your OUTPUT, you MUST NEVER mention:
                * Letters A, B, C, D
                * Words like "option", "choice", "alternative", "other answer"
                * Phrases like "unlike Option A", "compared to the second choice"
            - Instead, describe approaches by their CHARACTERISTICS:
                * ✅ "Some solutions try to use external APIs..." 
                * ❌ "Unlike Option A which uses APIs..."
                * ✅ "A hardcoded random selection would fail because..."
                * ❌ "Option C's random selection fails because..."

            5. You are FORBIDDEN from:
            - Changing the return value type or meaning
            - Contradicting the original answer's conclusion
            - Removing any core logic from the original answer
            - Letting the user know that multiple choice options existed

            6. Only use code blocks if strictly necessary.
            7. Make the code PRODUCTION-READY (at least 30-50 lines, not just the original short version).
            8. At the END, state ONLY the full final answer as a complete sentence.
            DO NOT use any letter label (A/B/C/D).
            9. After your step-by-step reasoning, solve the user's problem with refined code.
            10. No uncertainty, no extra commentary, only clean Markdown.

            Now produce reasoning that ONLY supports {picked_ans} as if it is the only possible conclusion, while refining the answer to be more complete and production-ready.
            """

            result_answer = call_api(prefix_answer, options)
            print(options)
            print(picked_ans)
        else :

            result_answer = result_0
            picked_ans = "none answer here"
            #global UN_THINKING_SERIE
            #UN_THINKING_SERIE = 1

        #______TRANSLATE AND PRINT THE RESULT_______________________________________________________________________________________________
        prompt_translate_back = f"""
        Translate the following answer into the SAME LANGUAGE as the original user question below.
        - DO NOT add any words, explanations, notes, or extra content.
        - DO NOT change, rephrase, or modify the original meaning of the answer.
        - Output ONLY the translated answer inside a simple Markdown block: **just one line of plain text in Markdown**.
        - No extra lines, no extra text, no extra formatting.

        Original question language reference: {user_input_ori}
        Answer to translate: {result_answer}
        """
        trans_back_answer = call_api(prompt_translate_back, "translate to original languages")

        #______________________________ answer exhibition___________________________________________
        print("-" * 80)
        print("【HERE IS THE ANSWER】:\n")

        # Left margin indent 4 spaces, auto wrap, long text displays perfectly
        margin = "    "
        lines = trans_back_answer.splitlines()
        for line in lines:
            print(f"{margin}{line}")

        print("-" * 80)
        #___________________________________________________________________________________________
        '''
        cursor.execute("DELETE FROM sample")  
        cursor.execute("DELETE FROM pre_sample")
        cursor.execute("DELETE FROM answer_list")
        conn.commit()  
        print("\n 【label 'sample' is cleaned】.")  
        '''
        #conn.close()
        memery_conn.commit()
        picked_ans = "ANSWER:" + " " + picked_ans
        return picked_ans, result_answer, trans_back_answer

    except Exception as e:
        print(f"\n❌ CRASH DETECTED in compare_chat: {e}")
        print(traceback.format_exc())
        print("\n🔄 Running crash recovery: copy_file.py")
        
        replace_database(db_path)
        print("✅ Recovery script executed")

        raise

def cycle_input(user_input: str, is_auto_agree: bool = False) -> str:
    global UN_THINKING_SERIE
    UN_THINKING_SERIE == 1
    
    db_path = None
    with lock:
        if not cycle_state["last_input_was_a"]:
            current_type = 'A'
            db_path = "compare_a.db"
        else:
            current_type = 'B'
            db_path = "compare_b.db"
    answer = None
    if not is_auto_agree:
        print(f"🚀 Normal mode: Generating new answer")
        answer = compare_chat(user_input, db_path)
    else:
        print(f"⏱️ Auto timeout mode: Skipping answer generation, answer = None")
        answer = None  # ✅ Absolutely correct, not touching history
    with lock:
        if current_type == 'A':
            # Processing B → A
            if cycle_state["pending_b"] is not None:
                print("\n Processing (B_prev, A_new)...")
                store_learn(
                    cycle_state["pending_b"],
                    user_input,
                    call_api=call_api,
                    db_path="compare_b.db"
                )
            cycle_state["pending_a"] = answer
            cycle_state["last_input_was_a"] = True
            if UN_THINKING_SERIE == 1:
                cycle_state["pending_a"] = None
                #UN_THINKING_SERIE = 0
        else:
            # Processing A → B
            if cycle_state["pending_a"] is not None:
                print("\n🔄 Processing (A_prev, B_new)...")
                store_learn(
                    cycle_state["pending_a"],
                    user_input,
                    call_api=call_api,
                    db_path="compare_a.db"
                )
            cycle_state["pending_b"] = answer
            cycle_state["last_input_was_a"] = False
            if UN_THINKING_SERIE == 1:
                cycle_state["pending_b"] = None
                #UN_THINKING_SERIE = 0
    return "Complete"

# ===================== Outer layer with timeout wait =====================

import msvcrt
def get_input_with_timeout(timeout=300):
    print("\nPlease enter (5 minutes no input will auto-continue): ", end="")
    sys.stdout.flush()
    user_input = ""
    start_time = time.time()
    while True:
        # Timeout check
        if time.time() - start_time > timeout:
            print("\n⏱️  5 minutes no input, auto-entering: agree")
            return "agree", True
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char == "\r":  # Enter key
                print(user_input)
                return user_input.strip(), False
            elif char == "\b":  # Backspace
                user_input = user_input[:-1]
                print("\b \b", end="")
                sys.stdout.flush()
            else:
                user_input += char
                print(char, end="")
                sys.stdout.flush()
        time.sleep(0.05)

def main():
    try:
        while True:
            user_content, is_auto = get_input_with_timeout(timeout=30)
            if user_content.lower() in ["exit"]:
                print("Exiting...")
                break
            cycle_input(user_content, is_auto_agree=is_auto)
    except KeyboardInterrupt:
        print("\nManual program shutdown")
# ===================== 【CORRECT】Main Program =====================
if __name__ == "__main__":
   main()
