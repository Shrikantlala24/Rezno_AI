/**
 * Sample research runs matching backend models:
 * SearchRun, RankedPaper, GraphNode, GraphEdge, Claim, Synthesis
 */
const MOCK_RUNS = [
  {
    id: "run-trans-01",
    query: "Attention mechanisms and parameter-efficient fine-tuning in LLMs",
    queries: [
      "Attention mechanisms parameter-efficient fine-tuning LLMs",
      "LoRA Low-rank adaptation transformer architectures",
      "FlashAttention memory efficient scaled dot product",
      "Prefix tuning adapter layers large language models"
    ],
    candidate_count: 84,
    status: "ok",
    search_error: null,
    timestamp: "14 Nov 2026 18:42",
    synthesis: {
      summary: `Parameter-efficient fine-tuning (PEFT) has emerged as the standard paradigm for adapting large language models without updating full parameter matrices. **LoRA (Low-Rank Adaptation)** decomposes weight updates into low-rank matrices \\( \\Delta W = B \\cdot A \\), reducing trainable parameters by up to 10,000x while maintaining downstream benchmark performance. Concurrently, memory and computational bottlenecks in standard attention are addressed by **FlashAttention**, which leverages GPU SRAM tiling to eliminate intermediate quadratic memory materialization. Together, these methods allow billion-parameter models to be fine-tuned and inferred on consumer-grade hardware.`,
      citations: ["2106.09685", "2205.14135", "1706.03762", "2110.04366"],
      claims: [
        {
          claim: "LoRA reduces trainable parameter count by 10,000x without quality loss.",
          arxiv_id: "2106.09685",
          supporting_sentence: "LoRA reduces the number of trainable parameters by 10,000 times and the GPU memory requirement by 3 times compared to full fine-tuning."
        },
        {
          claim: "FlashAttention scales linearly with sequence length in IO-complexity.",
          arxiv_id: "2205.14135",
          supporting_sentence: "FlashAttention tiles the softmax computation to minimize memory reads/writes between GPU HBM and SRAM."
        },
        {
          claim: "Multi-head attention allows joint attending to information from different representation subspaces.",
          arxiv_id: "1706.03762",
          supporting_sentence: "Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions."
        }
      ]
    },
    papers: [
      {
        arxiv_id: "2106.09685",
        title: "LoRA: Low-Rank Adaptation of Large Language Models",
        authors: ["Edward J. Hu", "Yelong Shen", "Phillip Wallis", "Zeyuan Allen-Zhu", "Yuanzhi Li", "Shean Wang", "Lu Wang", "Weizhu Chen"],
        author_line: "Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li et al.",
        summary: "An efficient adaptation approach that freezes pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture, greatly reducing storage requirements.",
        published: "2021-06-17",
        pdf_url: "https://arxiv.org/pdf/2106.09685.pdf",
        abs_url: "https://arxiv.org/abs/2106.09685",
        primary_category: "cs.CL",
        relevance_score: 0.942,
        status: "keep",
        note: "Core foundational paper for adapter architectures."
      },
      {
        arxiv_id: "2205.14135",
        title: "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        authors: ["Tri Dao", "Daniel Y. Fu", "Stefano Ermon", "Atri Rudra", "Christopher Ré"],
        author_line: "Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, Christopher Ré",
        summary: "Presents FlashAttention, an IO-aware exact attention algorithm that uses tiling to reduce memory reads/writes between GPU high bandwidth memory (HBM) and GPU on-chip SRAM.",
        published: "2022-05-27",
        pdf_url: "https://arxiv.org/pdf/2205.14135.pdf",
        abs_url: "https://arxiv.org/abs/2205.14135",
        primary_category: "cs.LG",
        relevance_score: 0.895,
        status: "keep",
        note: "Crucial for hardware speedup and long-context scaling."
      },
      {
        arxiv_id: "1706.03762",
        title: "Attention Is All You Need",
        authors: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"],
        author_line: "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones et al.",
        summary: "Proposes the Transformer network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        published: "2017-06-12",
        pdf_url: "https://arxiv.org/pdf/1706.03762.pdf",
        abs_url: "https://arxiv.org/abs/1706.03762",
        primary_category: "cs.CL",
        relevance_score: 0.881,
        status: "unreviewed",
        note: ""
      },
      {
        arxiv_id: "2110.04366",
        title: "Prefix-Tuning: Optimizing Continuous Prompts for Generation",
        authors: ["Xiang Lisa Li", "Percy Liang"],
        author_line: "Xiang Lisa Li, Percy Liang",
        summary: "Prepends continuous task-specific virtual tokens to input sequences, keeping language model parameters frozen while tuning prompt prefixes.",
        published: "2021-10-08",
        pdf_url: "https://arxiv.org/pdf/2110.04366.pdf",
        abs_url: "https://arxiv.org/abs/2110.04366",
        primary_category: "cs.CL",
        relevance_score: 0.812,
        status: "maybe",
        note: "Contrast with LoRA approach."
      }
    ],
    graph: {
      nodes: [
        { id: "2106.09685", label: "LoRA Adaptation (2106.09685)", type: "paper", pdf_url: "https://arxiv.org/pdf/2106.09685.pdf", abs_url: "https://arxiv.org/abs/2106.09685" },
        { id: "2205.14135", label: "FlashAttention (2205.14135)", type: "paper", pdf_url: "https://arxiv.org/pdf/2205.14135.pdf", abs_url: "https://arxiv.org/abs/2205.14135" },
        { id: "1706.03762", label: "Attention Is All You Need (1706.03762)", type: "paper", pdf_url: "https://arxiv.org/pdf/1706.03762.pdf", abs_url: "https://arxiv.org/abs/1706.03762" },
        { id: "2110.04366", label: "Prefix-Tuning (2110.04366)", type: "paper", pdf_url: "https://arxiv.org/pdf/2110.04366.pdf", abs_url: "https://arxiv.org/abs/2110.04366" },
        { id: "c-peft", label: "Parameter-Efficient Fine-Tuning", type: "concept" },
        { id: "c-lora", label: "Low-Rank Adaptation", type: "concept" },
        { id: "c-flash", label: "IO-Aware Tiling", type: "concept" },
        { id: "c-mha", label: "Multi-Head Attention", type: "concept" },
        { id: "c-kv", label: "KV Cache Optimization", type: "concept" },
        { id: "c-sram", label: "GPU SRAM Utilization", type: "concept" }
      ],
      edges: [
        { source: "2106.09685", target: "c-peft", type: "MENTIONS" },
        { source: "2106.09685", target: "c-lora", type: "MENTIONS" },
        { source: "2110.04366", target: "c-peft", type: "MENTIONS" },
        { source: "2205.14135", target: "c-flash", type: "MENTIONS" },
        { source: "2205.14135", target: "c-sram", type: "MENTIONS" },
        { source: "1706.03762", target: "c-mha", type: "MENTIONS" },
        { source: "c-flash", target: "c-kv", type: "SIMILAR_TO" },
        { source: "c-lora", target: "c-peft", type: "SIMILAR_TO" },
        { source: "2106.09685", target: "1706.03762", type: "SIMILAR_TO" },
        { source: "2205.14135", target: "1706.03762", type: "SIMILAR_TO" }
      ]
    }
  },
  {
    id: "run-quant-02",
    query: "Post-training quantization and 4-bit weight compression in Transformers",
    queries: [
      "Post-training quantization 4-bit weights LLMs",
      "AWQ activation-aware weight quantization",
      "GPTQ accurate post-training quantization transformers"
    ],
    candidate_count: 62,
    status: "ok",
    search_error: null,
    timestamp: "14 Nov 2026 19:15",
    synthesis: {
      summary: `Post-training quantization (PTQ) enables executing 70B+ parameter models on resource-constrained devices without extensive retraining. Methods such as **AWQ (Activation-aware Weight Quantization)** observe that preserving only 1% of salient weights protects output fidelity, enabling uniform 4-bit integer weights. Similarly, **GPTQ** utilizes second-order Taylor expansion approximations to quantize layer weights in hours. Both methodologies minimize memory bandwidth saturation while preserving perplexity.`,
      citations: ["2306.00978", "2210.17323", "2106.09685"],
      claims: [
        {
          claim: "Protecting 1% of salient weights is sufficient to retain full 16-bit FP accuracy in 4-bit weights.",
          arxiv_id: "2306.00978",
          supporting_sentence: "AWQ shows that weight quantization error is largely dominated by salient activations, which can be protected by per-channel scaling."
        },
        {
          claim: "GPTQ achieves 4-bit quantization with minimal loss in perplexity in a single GPU day.",
          arxiv_id: "2210.17323",
          supporting_sentence: "GPTQ efficiently solves the layer-wise quantization problem using inverse Hessian updates."
        }
      ]
    },
    papers: [
      {
        arxiv_id: "2306.00978",
        title: "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration",
        authors: ["Ji Lin", "Jiaming Tang", "Haotian Tang", "Shang Yang", "Xingyu Dang", "Song Han"],
        author_line: "Ji Lin, Jiaming Tang, Haotian Tang, Shang Yang, Xingyu Dang et al.",
        summary: "Proposes Activation-aware Weight Quantization (AWQ) based on the observation that protecting salient weights corresponding to large activation magnitudes prevents degradation.",
        published: "2023-06-01",
        pdf_url: "https://arxiv.org/pdf/2306.00978.pdf",
        abs_url: "https://arxiv.org/abs/2306.00978",
        primary_category: "cs.LG",
        relevance_score: 0.931,
        status: "keep",
        note: "Fast inference on edge GPUs."
      },
      {
        arxiv_id: "2210.17323",
        title: "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers",
        authors: ["Elias Frantar", "Saleh Ashkboos", "Torsten Hoefler", "Dan Alistarh"],
        author_line: "Elias Frantar, Saleh Ashkboos, Torsten Hoefler, Dan Alistarh",
        summary: "An efficient post-training quantization method based on approximate second-order information that scales to 175 billion parameter models.",
        published: "2022-10-31",
        pdf_url: "https://arxiv.org/pdf/2210.17323.pdf",
        abs_url: "https://arxiv.org/abs/2210.17323",
        primary_category: "cs.LG",
        relevance_score: 0.908,
        status: "unreviewed",
        note: ""
      },
      {
        arxiv_id: "2106.09685",
        title: "LoRA: Low-Rank Adaptation of Large Language Models",
        authors: ["Edward J. Hu", "Yelong Shen", "Phillip Wallis", "Zeyuan Allen-Zhu", "Yuanzhi Li", "Weizhu Chen"],
        author_line: "Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li et al.",
        summary: "An efficient adaptation approach that freezes pre-trained model weights and injects trainable rank decomposition matrices into each layer.",
        published: "2021-06-17",
        pdf_url: "https://arxiv.org/pdf/2106.09685.pdf",
        abs_url: "https://arxiv.org/abs/2106.09685",
        primary_category: "cs.CL",
        relevance_score: 0.774,
        status: "keep",
        note: "Used in QLoRA combined with 4-bit NormalFloat."
      }
    ],
    graph: {
      nodes: [
        { id: "2306.00978", label: "AWQ Quantization (2306.00978)", type: "paper", pdf_url: "https://arxiv.org/pdf/2306.00978.pdf", abs_url: "https://arxiv.org/abs/2306.00978" },
        { id: "2210.17323", label: "GPTQ Quantization (2210.17323)", type: "paper", pdf_url: "https://arxiv.org/pdf/2210.17323.pdf", abs_url: "https://arxiv.org/abs/2210.17323" },
        { id: "2106.09685", label: "LoRA (2106.09685)", type: "paper", pdf_url: "https://arxiv.org/pdf/2106.09685.pdf", abs_url: "https://arxiv.org/abs/2106.09685" },
        { id: "c-ptq", label: "Post-Training Quantization", type: "concept" },
        { id: "c-4bit", label: "4-bit Weight Compression", type: "concept" },
        { id: "c-salient", label: "Salient Activation Protection", type: "concept" },
        { id: "c-peft", label: "Parameter-Efficient Fine-Tuning", type: "concept" }
      ],
      edges: [
        { source: "2306.00978", target: "c-ptq", type: "MENTIONS" },
        { source: "2306.00978", target: "c-4bit", type: "MENTIONS" },
        { source: "2306.00978", target: "c-salient", type: "MENTIONS" },
        { source: "2210.17323", target: "c-ptq", type: "MENTIONS" },
        { source: "2210.17323", target: "c-4bit", type: "MENTIONS" },
        { source: "2106.09685", target: "c-peft", type: "MENTIONS" },
        { source: "c-ptq", target: "c-peft", type: "SIMILAR_TO" },
        { source: "2306.00978", target: "2210.17323", type: "SIMILAR_TO" }
      ]
    }
  }
];

const MOCK_MESSAGES = [
  {
    id: "msg-01",
    role: "user",
    content: "Attention mechanisms and parameter-efficient fine-tuning in LLMs",
    intent: "new_search"
  },
  {
    id: "msg-02",
    role: "assistant",
    content: MOCK_RUNS[0].synthesis.summary,
    search_run_id: "run-trans-01",
    is_unsourced: false,
    is_fallback: false,
    claims: MOCK_RUNS[0].synthesis.claims
  }
];

