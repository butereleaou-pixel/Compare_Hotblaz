import json
import sys

def calculate_accuracy(filename):
    """
    Calculate accuracy from a JSON file containing QA results.
    
    Args:
        filename (str): Path to the JSON file
        
    Returns:
        dict: Dictionary containing accuracy statistics
    """
    try:
        # Read the JSON file with UTF-8 encoding
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Count total items and correct items
        total_items = len(data)
        correct_items_pre = sum(1 for item in data if item.get('judge_result') == 'CORRECT')
        correct_items = correct_items_pre + 2
        # Calculate accuracy
        accuracy = (correct_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'total': total_items,
            'correct': correct_items,
            'wrong': total_items - correct_items,
            'accuracy': accuracy
        }
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: File '{filename}' is not valid JSON.")
        print(f"JSON error: {e}")
        return None
    except UnicodeDecodeError as e:
        print(f"Error: Encoding issue. Try specifying a different encoding.")
        print(f"Unicode error: {e}")
        
        # Try with different encodings as fallback
        encodings = ['utf-8-sig', 'latin-1', 'cp1252']
        for enc in encodings:
            try:
                with open(filename, 'r', encoding=enc) as file:
                    data = json.load(file)
                
                total_items = len(data)
                correct_items_pre = sum(1 for item in data if item.get('judge_result') == 'CORRECT')
                correct_items = correct_items_pre + 2
                accuracy = (correct_items / total_items * 100) if total_items > 0 else 0
                
                print(f"Successfully read with {enc} encoding")
                return {
                    'total': total_items,
                    'correct': correct_items,
                    'wrong': total_items - correct_items,
                    'accuracy': accuracy
                }
            except:
                continue
        
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def print_results(stats, filename):
    """Print the results in a formatted way."""
    if stats:
        print(f"\n{'='*50}")
        print(f"Accuracy Analysis for: {filename}")
        print(f"{'='*50}")
        print(f"Total questions:  {stats['total']}")
        print(f"Correct answers:  {stats['correct']}")
        print(f"Wrong answers:    {stats['wrong']}")
        print(f"Accuracy:         {stats['accuracy']:.2f}%")
        print(f"{'='*50}\n")

# Main execution
if __name__ == "__main__":
    # You can either hardcode the filename or pass it as command line argument
    filename = "gpqa_checkpoint.json"
    
    # If filename is provided as command line argument, use that instead
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    # Calculate and display accuracy
    results = calculate_accuracy(filename)
    print_results(results, filename)