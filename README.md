<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/68ff189643ff73230742fecd/6lGZiEvfvADsZzkRZu68c.png" width="400" alt="logo">
</div>

<div align="center" style="line-height: 1;">
  <a href="mailto:mark@hotblaz.com" target="_blank" style="margin: 2px;">
    <img alt="Email" src="https://img.shields.io/badge/Email-mark@hotblaz.com-D14836?logo=gmail&logoColor=white&color=D14836" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://www.hotblaz.com" target="_blank" style="margin: 2px;">
    <img alt="Website" src="https://img.shields.io/badge/Website-hotblaz.com-FFD700?logo=googlechrome&logoColor=white&color=FFD700" style="display: inline-block; vertical-align: middle;"/>
  </a>
  <a href="https://x.com/Mark_Leou" target="_blank" style="margin: 2px;">
  <img alt="X" src="https://img.shields.io/badge/Follow On X-000000?logo=x&logoColor=white" style="display: inline-block; vertical-align: middle;"/>
  </a>
</div>

<hr>

# 1. Preface

- Anti_9 is an RL layer applied to LLMs. It employs the concept of "comparison" to endow the model with multidimensional consciousness. General intelligence is fundamentally rooted in comparison: from deep machine learning to our daily decision-making, comparison serves as the most fundamental lever for the emergence of intelligence. Consider why you chose to wear a T-shirt this morning, or why you decided to buy it in the first place. Although many researchers have devoted enormous efforts to AI analogical reasoning, and techniques such as k-clustering and graph classification have long been used in unsupervised learning, we still believe that Anti_9 represents a viable implementation for LLMs.

# 2. Benchmark

<div align="center">
  <div style="display: flex; justify-content: center; gap: 20px;">
    <img src="https://cdn-uploads.huggingface.co/production/uploads/68ff189643ff73230742fecd/2YV_X9CfouwB703EdGRLp.png" width="750" alt="curve">
  </div>
  <br>
  <tr>
    <td>Compared original base leaderboard data from</td>
  </tr>
  <tr>
    <td><a href="https://artificialanalysis.ai/evaluations/gpqa-diamond">artificialanalysis</a></td>
  </tr>
</div>

- We optimized the base model Deepseek-V3.2-thinking by <font color="blue">6.54%</font> with a base score of <font color="blue">85.86%</font>, reaching a final score of <font color="blue">92.4%</font>, which is top 3 among LLMs worldwide.
- The test record is on GitHub. You can click [here](https://github.com/butereleaou-pixel/Compare_Hotblaz/tree/cd17a17548cf67b9683dcabce525b31e6a024ea1/test_record) to check.

# 3. Quick Start

#### 1. General Use

For quick start:

- Basic environment:

```shell
python 3.10
cuda 121
torch 2.5.1
numpy 2.1.2
```

```shell
git clone https://github.com/butereleaou-pixel/Compare_Hotblaz.git
```

```shell
pip install requirements.txt
```

```shell
pip install hotblaz
```
- Download the embedding model `model.safetensors` ([download](https://huggingface.co/Hotblaz/Compare_Anti_9/resolve/main/gpt2_model/model.safetensors?download=true)) and answer analysis model `final_model_after_ctrlc_282929230424223_916.pth` ([download](https://huggingface.co/Hotblaz/Compare_Anti_9/resolve/main/model_core/model_pth/final_model_after_ctrlc_282929230424223_916.pth?download=true)) from HuggingFace.
- Put embedding model into `gpt2_local` and put answer analysis model into `model_core/model_pth`

- Find the file `llm_api`, and fill in your real parameters: `YOUR_MODEL_API_ADDRESS`, `YOUR_REAL_API_TOKEN`, `YOUR_REAL_MODEL_TYPE`

```python
def call_api(system_prompt, user_content):
  
    url = "https://YOUR_MODEL_API_ADDRESS"
  
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_REAL_API_TOKEN"
    }
  
    data = {
        "model": "YOUR_REAL_MODEL_TYPE",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": temperature,
        "stream": False
    }
  
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result_json = response.json()
    return result_json["choices"][0]["message"]["content"]
```

- If you want to use the chat UI:

```shell
python web_chat_ui.py
```

- You will have a web UI dialog like other LLMs.

<div align="center">
  <div style="display: flex; justify-content: center; gap: 20px;">
    <img src="https://cdn-uploads.huggingface.co/production/uploads/68ff189643ff73230742fecd/nEawGG9Zmsv2oP-NbcySe.png" width="550" alt="curve1">
  </div>
  <br>
  <span style="font-size:15px; font-weight:500;">Normal response</span>
</div>

<div align="center">
  <div style="display: flex; justify-content: center; gap: 20px;">
    <img src="https://cdn-uploads.huggingface.co/production/uploads/68ff189643ff73230742fecd/0mSvzCabJse1JWaSjkKDc.png" width="550" alt="curve2">
  </div>
  <br>
  <span style="font-size:15px; font-weight:500;">Compare think response</span>
</div>

- The response has two modes. The first is normal mode for simple questions. The second is Compare Think mode. If the question requires reasoning or deep research, the chat will automatically enter that mode. You will need to wait a few minutes while the little animation plays.

- The speed depends on your base model and the parameters (`max_tasks`, `parallel_limit`, `max_worker`) you set in `config_adjust.json`. Normally, avoid using a thinking mode model API, or use a deployed open-source model in a GPU-deprived environment. Also, watch for the burst limit; otherwise, you may spend more time and not get the correct comparison result.

```json
{
  "generate": {
    "mean_line_ratio": 0.880,
    "ignore_count": 3,
    "pre_sample_parallel_limit": 7,
    "sample_max_tasks": 8,
    "sample_parallel_limit": 7,
    "answer_max_worker": 9,
    "temperature": 0.934,
    "temperature_compare": 0.795,
    "model_path": "model_core/model_pth/final_model_after_ctrlc_282929230424223_916.pth"
  }
}
```

- If you want to rerun the GPQA test:

```shell
python GPQA.py
```

- The dataset has been automatically set into the process. You can use `check_result.json` to select the questions you want to test. You can also change these settings for other benchmarks.

- This architecture is designed for predicting facts. You can ask it about real scenarios in your daily life with real details but missing results. For example: ask about hidden facts. Try it with a base model without Anti_9 and see the difference.

#### 2. Professional Use

- We have a multidimensional architecture and a small transformer in the final judgment part. You can train this model with your own chat data.

- First, set up the data pipeline:

```shell
cd model_core
```

```shell
mul_p_b.py -> save_data.py -> pipeline.py
```

- Train with your preprocessed data. Be careful with the model dimension; the data we currently have may not be sufficient for a larger model.

```shell
python trainin.py
```

# 4. How It Works

<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/68ff189643ff73230742fecd/aObxLVXktjNug-vztQ9Mp.png" width="600" alt="anti_9_compare">
</div>

#### 1. Parallel Generation of Samples

- Instead of directly generating the answer or using reasoning as one-dimensional thinking, we make the LLM generate several compare samples as guide tokens. This allows the LLM to have a degree of association away from the original question. To simulate how humans gain experience and form unique character, we implement memory as token heads during the generation of compare samples. Although more samples will make the generated result more accurate in the final analytic process, we limited it to 40 compare samples and 30 pre-compare samples in this project, considering FLOPs consumption.

#### 2. Pre-memory

- For this part, you can check on HuggingFace [here](https://huggingface.co/Hotblaz/Compare_Anti_9)

#### 3. Final Result

**Euclidean Distance:**
**Create Multidimension for Small Transformer:**
**Benchmark Test:**

- For this part, you can check on HuggingFace [here](https://huggingface.co/Hotblaz/Compare_Anti_9)

# 5. Base Models

<div align="center">
  <table>
    <thead>
      <tr>
        <th>Model</th>
        <th>Task</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="https://huggingface.co/deepseek-ai/DeepSeek-V3.2">deepseek-v3.2-thinking</a></td>
        <td>Answer generation</td>
      </tr>
      <tr>
        <td>ernie-4.5</td>
        <td>Sample generation</td>
      </tr>
      <tr>
        <td><a href="https://huggingface.co/zai-org/GLM-4.7">glm-4.7</a></td>
        <td>Final answer analysis</td>
      </tr>
    </tbody>
  </table>
</div>

# 6. License

This repository and the model weights are licensed under the MIT License.

# 7. Final Words

- Our next task will be the ARC Prize. I would be glad if you try this Compare Anti_9 on other benchmarks. If you do, please leave a score here:

| Leaderboard Name | Score |
|-----------------|-------|
|                 |       |
