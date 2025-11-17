# ⚡ Agent Lightning Integration Guide

Transform Tongyi Agent from a static tool-based agent into a **learning, adaptive research assistant** with Microsoft's Agent Lightning framework.

## 🚀 What is Agent Lightning?

**Agent Lightning** is Microsoft's framework that turns ANY AI agent into an optimizable beast with **ZERO CODE CHANGE**. It enables:

- **Reinforcement Learning**: Optimize agent decision-making
- **Automatic Prompt Optimization**: Improve system prompts automatically
- **Supervised Fine-tuning**: Learn from expert demonstrations
- **Universal Compatibility**: Works with any agent framework

## 🎯 Benefits for Tongyi Agent

### **Zero Code Change Integration**
- Wrap existing Tongyi and Claude SDK orchestrators
- Preserve all current research capabilities
- Add learning without rewriting code

### **Adaptive Research Workflows**
- **Better Tool Selection**: Learn which tools work best for different scenarios
- **Optimized Query Planning**: Improve multi-step research strategies
- **Domain Specialization**: Fine-tune for specific research fields

### **Performance Optimization**
- **Reduced API Costs**: Learn to be more efficient with tool calls
- **Faster Response Times**: Optimize decision-making speed
- **Better Error Handling**: Learn from failed research attempts

## 📦 Installation

### **Option 1: Install with Agent Lightning (Recommended)**
```bash
# Install with full training capabilities
pip install -e ".[agent-lightning]"

# Or install manually
pip install agentlightning torch transformers
```

### **Option 2: Standard Installation**
```bash
# Standard installation without training
pip install -e "."
```

## ⚙️ Configuration

### **Training Configuration (`training_config.ini`)**

```ini
[training]
enabled = false
mode = "prompt"  # "prompt", "rl", "sft"
training_data_path = ".tongyi_training"

[prompt_optimization]
iterations = 100
optimization_target = "research_efficiency"
use_history = true
history_size = 50
```

### **Environment Variables**
```bash
# Enable training mode
export TONGYI_TRAINING_ENABLED=true

# Set optimization mode
export TONGYI_TRAINING_MODE=prompt

# Training data location
export TONGYI_TRAINING_PATH=./my_training_data
```

## 🎮 Usage

### **1. Enable Training Mode**
```bash
# Use training with default settings
tongyi-cli --train "your research question"

# Specify optimization mode
tongyi-cli --train --training-mode rl "complex research query"

# Claude SDK with training
tongyi-cli --train --training-mode prompt "analyze this code"
```

### **2. Training Modes**

#### **🎯 Prompt Optimization (Default)**
```bash
tongyi-cli --train --training-mode prompt "How does this algorithm work?"
```
- Automatically improves system prompts
- Learns from interaction history
- Best for improving response quality

#### **🧠 Reinforcement Learning**
```bash
tongyi-cli --train --training-mode rl "Compare these research papers"
```
- Optimizes decision-making policies
- Uses custom reward functions
- Best for complex research strategies

#### **📚 Supervised Fine-tuning**
```bash
tongyi-cli --train --training-mode sft "What are the key findings?"
```
- Learns from expert examples
- Improves specific capabilities
- Best for domain specialization

### **3. Training Management**

#### **Check Training Status**
```bash
tongyi-cli --training-stats
```

#### **Run Optimization**
```bash
# Run 100 optimization iterations
tongyi-cli --optimize --optimize-iterations 100

# Run with specific optimization type
tongyi-cli --optimize --optimize-iterations 200
```

#### **Export Training Data**
```bash
# Export all training data
tongyi-cli --export-training-data my_training_data.json

# Use exported data for analysis or sharing
```

## 🔧 Advanced Configuration

### **Custom Reward Functions**

Create custom reward functions for RL training:

```python
# In optimized_claude_agent.py or optimized_tongyi_agent.py
def _custom_reward_function(self, query: str, response: str, tools_used: List[str]) -> float:
    reward = 0.0

    # Reward for comprehensive analysis
    if len(response) > 1000:
        reward += 0.2

    # Reward for tool diversity
    reward += 0.3 * len(set(tools_used))

    # Reward for citations
    if "http" in response or "doi" in response:
        reward += 0.2

    return reward
```

### **Training Targets**

Configure what to optimize:

```ini
[prompt_optimization]
optimization_target = "research_efficiency"  # Options:
# research_efficiency - Focus on research quality
# response_quality - Focus on response completeness
# tool_usage - Focus on tool selection efficiency
# response_speed - Focus on faster responses
```

### **Performance Thresholds**

Set optimization goals:

```ini
[performance_metrics]
max_response_time = 30.0
min_success_rate = 0.8
min_tool_efficiency = 0.6
```

## 📊 Monitoring & Analytics

### **Performance Metrics**
- **Total Interactions**: Number of training queries processed
- **Success Rate**: Percentage of successful research outcomes
- **Response Time**: Average time per query
- **Tool Usage Efficiency**: Effectiveness of tool selection
- **Training Progress**: Optimization improvement over time

### **Training Data Structure**
```json
{
  "timestamp": 1701234567.89,
  "query": "Analyze this research paper",
  "response": "The paper presents...",
  "response_time": 3.2,
  "claude_success": true,
  "tools_used": ["Read", "Grep", "WebSearch"],
  "query_length": 24,
  "response_length": 1250
}
```

### **Export Analysis**
```bash
# Export and analyze training data
tongyi-cli --export-training-data analysis.json

# Use external tools for analysis
python -c "
import json
with open('analysis.json') as f:
    data = json.load(f)
print(f'Total interactions: {len(data[\"interactions\"])}')
print(f'Average response time: {data[\"metrics\"][\"average_response_time\"]:.2f}s')
"
```

## 🎓 Training Workflows

### **1. Initial Training (First Session)**
```bash
# Start with prompt optimization
tongyi-cli --train --training-mode prompt "basic research queries"

# Use for 20-50 interactions
tongyi-cli --train "what is machine learning?"
tongyi-cli --train "analyze this algorithm"
# ... more queries

# Run optimization
tongyi-cli --optimize --optimize-iterations 50
```

### **2. Advanced Training**
```bash
# Switch to RL for complex strategies
tongyi-cli --train --training-mode rl "multi-step research tasks"

# Use for specialized domains
tongyi-cli --train --training-mode sft "domain-specific questions"
```

### **3. Continuous Improvement**
```bash
# Regular training sessions
tongyi-cli --train "daily research tasks"

# Periodic optimization
tongyi-cli --optimize --optimize-iterations 100

# Export for backup
tongyi-cli --export-training-data backup_$(date +%Y%m%d).json
```

## 🛠️ Troubleshooting

### **Common Issues**

#### **Agent Lightning Not Available**
```bash
❌ Optimized agents not available: No module named 'agentlightning'
```
**Solution:**
```bash
pip install agentlightning torch transformers
```

#### **Training Data Not Found**
```bash
ℹ️ No training data found. Run with --train to generate training data first.
```
**Solution:**
```bash
tongyi-cli --train "generate some training data"
```

#### **Optimization Fails**
```bash
❌ Optimization failed
```
**Solution:**
- Check you have enough training data (10+ interactions)
- Verify training configuration
- Try fewer iterations: `--optimize-iterations 50`

### **Debug Mode**

Enable debug logging:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -m tongyi_agent.cli --train --training-mode prompt "test query" --verbose
```

### **Reset Training**

Clear training data and start fresh:
```bash
rm -rf .tongyi_training
rm -rf .claude_training
```

## 📈 Performance Optimization

### **Memory Management**
- Training data auto-saves every 10 interactions
- Large training datasets are automatically chunked
- Memory usage scales linearly with interaction count

### **Speed Optimization**
- Use `prompt` mode for fastest learning
- Limit optimization iterations for quick improvements
- Export and analyze data offline for complex analysis

### **Cost Optimization**
- Agent Lightning reduces API calls over time through learning
- Monitor tool usage efficiency to track cost savings
- Use training data to identify expensive patterns

## 🔬 Research-Specific Features

### **Academic Research Optimization**
- **Citation Quality**: Learns to find and cite relevant sources
- **Analysis Depth**: Improves comprehensive analysis capabilities
- **Source Diversity**: Encourages using multiple information sources

### **Code Research Enhancement**
- **Tool Selection**: Learns best tools for different code analysis tasks
- **Pattern Recognition**: Improves code understanding and explanation
- **Debugging Strategy**: Optimizes approach to code problem-solving

### **Multi-modal Learning**
- **Text + Code**: Learns from mixed research queries
- **Web + Local**: Optimizes use of both web and local resources
- **Interactive + Batch**: Works with both real-time and batch research

## 🎯 Best Practices

### **Training Data Quality**
- Use diverse research queries
- Include both simple and complex tasks
- Mix different domains and topics
- Ensure consistent query formulation

### **Optimization Strategy**
1. **Start with prompt optimization** (fastest improvements)
2. **Progress to RL** for complex strategies
3. **Use SFT** for domain specialization
4. **Regular maintenance** with periodic optimization

### **Performance Monitoring**
- Check training stats weekly
- Export data monthly for analysis
- Monitor tool usage efficiency
- Track cost savings over time

## 🔗 Integration Examples

### **Python API Usage**
```python
from training_manager import get_training_manager

# Create training manager
manager = get_training_manager()

# Create optimized agent
agent = manager.create_optimized_agent(
    agent_type="claude",
    optimization_mode="prompt",
    enable_training=True
)

# Use agent with learning
response = await agent.process_query("your research query")

# Run optimization
manager.run_optimization(agent, iterations=100)

# Export data
manager.export_training_data(agent, "my_data.json")
```

### **Custom Training Session**
```python
# Custom training with specific queries
training_queries = [
    "What are the latest developments in NLP?",
    "Analyze this research paper methodology",
    "Compare these two algorithms",
    # ... more queries
]

session_results = manager.run_training_session(
    agent_type="claude",
    queries=training_queries,
    optimization_iterations=200
)

print(f"Training completed: {session_results['success']}")
print(f"Queries processed: {session_results['queries_processed']}")
```

## 🏆 Advanced Features

### **A/B Testing**
Compare standard vs optimized agents:
```ini
[experiments]
enable_ab_testing = true
control_ratio = 0.5
experiment_duration = 100
```

### **Scheduled Optimization**
Automatic optimization triggers:
```ini
[optimization_schedule]
schedule = "periodic"
periodic_interval = 100
trigger_on_performance_drop = true
performance_threshold = 0.7
```

### **Custom Metrics**
Add domain-specific metrics:
```python
def _research_quality_metric(self, query: str, response: str) -> float:
    # Custom research quality evaluation
    citations = response.count("http") + response.count("doi")
    analysis_depth = len(response.split("\n"))
    return (citations * 0.3) + (analysis_depth * 0.7)
```

## 🎓 Learning Resources

### **Agent Lightning Documentation**
- [Official Agent Lightning Repo](https://github.com/microsoft/agent-lightning)
- [Training Algorithms](https://microsoft.github.io/agent-lightning/stable/algorithms/)
- [API Reference](https://microsoft.github.io/agent-lightning/stable/api/)

### **Tongyi Agent Extensions**
- [Base Tongyi Agent](README.md)
- [Claude SDK Integration](OPENROUTER_INTEGRATION_SUMMARY.md)
- [Model Configuration](models.ini)

---

## 🚀 Next Steps

1. **Install Agent Lightning**: `pip install agentlightning torch transformers`
2. **Start Basic Training**: `tongyi-cli --train "your first research query"`
3. **Monitor Progress**: `tongyi-cli --training-stats`
4. **Optimize Performance**: `tongyi-cli --optimize`
5. **Export & Analyze**: `tongyi-cli --export-training-data data.json`

**Transform your Tongyi Agent into a learning, adaptive research assistant today!** ⚡

---

*This integration brings the power of Microsoft's Agent Lightning to Tongyi Agent, enabling continuous learning and optimization for research excellence.*