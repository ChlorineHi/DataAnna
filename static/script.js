function getLuckyNumber() {
    fetch('/lucky_number')
        .then(response => response.json())
        .then(data => {
            document.getElementById('lucky-number-result').textContent = 
                `您的幸运数字是: ${data.number}`;
        });
}

function getCurrentTime() {
    fetch('/current_time')
        .then(response => response.json())
        .then(data => {
            document.getElementById('current-time-result').textContent = 
                `当前时间: ${data.time}`;
        });
}

function analyzeText() {
    const text = document.getElementById('text-input').value;
    if (!text) {
        alert('请输入文本');
        return;
    }

    fetch(`/analyze_text/${encodeURIComponent(text)}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('text-analysis-result').textContent = 
                `文本分析结果:
- 文本长度: ${data.length}
- 单词数量: ${data.words}
- 大写字母数: ${data.uppercase_count}`;
        });
}
