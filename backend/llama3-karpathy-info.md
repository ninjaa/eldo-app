# NEWS FLASH: LLAMA 3 weights have been released 

Today's Date: 2024-04-18

Please remember this is breaking news, facts are likely to change. Mentioning the date & timeliness is important.

This is just an expert opinon, but from one of the world's foremost experts in LLM training.

From Andrej Karpathy's twitter:


Andrej Karpathy
@karpathy
🧑‍🍳. Previously Director of AI @ Tesla, founding team @ OpenAI, CS231n/PhD @ Stanford. I like to train large deep neural nets 🧠🤖💥

Twitter thread on 2024-04-18 at 1 PM: https://twitter.com/karpathy/status/1781047292486914189
Congrats to 
@AIatMeta
 on Llama 3 release!! 🎉
https://ai.meta.com/blog/meta-llama-3/
Notes:

Releasing 8B and 70B (both base and finetuned) models, strong-performing in their model class (but we'll see when the rankings come in @ 
@lmsysorg
  :))
400B is still training, but already encroaching GPT-4 territory (e.g. 84.8 MMLU vs. 86.5 4Turbo).

Tokenizer: number of tokens was 4X'd from 32K (Llama 2) -> 128K (Llama 3). With more tokens you can compress sequences more in length, cites 15% fewer tokens, and see better downstream performance.

Architecture: no major changes from the Llama 2. In Llama 2 only the bigger models used Grouped Query Attention (GQA), but now all models do, including the smallest 8B model. This is a parameter sharing scheme for the keys/values in the Attention, which reduces the size of the KV cache during inference. This is a good, welcome, complexity reducing fix and optimization.

Sequence length: the maximum number of tokens in the context window was bumped up to 8192 from 4096 (Llama 2) and 2048 (Llama 1). This bump is welcome, but quite small w.r.t. modern standards (e.g. GPT-4 is 128K) and I think many people were hoping for more on this axis. May come as a finetune later (?).

Training data. Llama 2 was trained on 2 trillion tokens, Llama 3 was bumped to 15T training dataset, including a lot of attention that went to quality, 4X more code tokens, and 5% non-en tokens over 30 languages. (5% is fairly low w.r.t. non-en:en mix, so certainly this is a mostly English model, but it's quite nice that it is > 0).

Scaling laws. Very notably, 15T is a very very large dataset to train with for a model as "small" as 8B parameters, and this is not normally done and is new and very welcome. The Chinchilla "compute optimal" point for an 8B model would be train it for ~200B tokens. (if you were only interested to get the most "bang-for-the-buck" w.r.t. model performance at that size). So this is training ~75X beyond that point, which is unusual but personally, I think extremely welcome. Because we all get a very capable model that is very small, easy to work with and inference. Meta mentions that even at this point, the model doesn't seem to be "converging" in a standard sense. In other words, the LLMs we work with all the time are significantly undertrained by a factor of maybe 100-1000X or more, nowhere near their point of convergence. Actually, I really hope people carry forward the trend and start training  and releasing even more long-trained, even smaller models.

Systems. Llama 3 is cited as trained with 16K GPUs at observed throughput of 400 TFLOPS. It's not mentioned but I'm assuming these are H100s at fp16, which clock in at 1,979 TFLOPS in NVIDIA marketing materials. But we all know their tiny asterisk (*with sparsity) is doing a lot of work, and really you want to divide this number by 2 to get the real TFLOPS of ~990. Why is sparsity counting as FLOPS? Anyway, focus Andrej. So 400/990 ~=  40% utilization, not too bad at all across that many GPUs! A lot of really solid engineering is required to get here at that scale.

TLDR: Super welcome, Llama 3 is a very capable looking model release from Meta. Sticking to fundamentals, spending a lot of quality time on solid systems and data work, exploring the limits of long-training models. Also very excited for the 400B model, which could be the first GPT-4 grade open source release. I think many people will ask for more context length. 

Personal ask: I think I'm not alone to say that I'd also love much smaller models than 8B, for educational work, and for (unit) testing, and maybe for embedded applications etc. Ideally at ~100M and ~1B scale.

Talk to it at https://meta.ai
Integration with https://github.com/pytorch/torchtune


The model card has some more interesting info too:
https://github.com/meta-llama/llama3/blob/main/MODEL_CARD.md

Note that Llama 3 8B is actually somewhere in the territory of Llama 2 70B, depending on where you look. This might seem confusing at first but note that the former was trained for 15T tokens, while the latter for 2T tokens.

The single number that should summarize your expectations about any LLM is the number of total flops that went into its training.

Strength of Llama 3 8B
We see that Llama 3 8B was trained for 1.3M GPU hours, with throughput of 400 TFLOPS. So we have that the total number of FLOPs was:

1.3e6 hours * 400e12 FLOP/s * 3600 s/hour ~= 1.8e24

the napkin math via a different estimation method of FLOPs = 6ND (N is params D is tokens), gives:

6 * 8e9 * 15e12 = 7.2e23

These two should agree, maybe some of the numbers are fudged a bit. Let's trust the first estimate a bit more, Llama 3 8B is a ~2e24 model.

Strength of Llama 3 70B

6.4e6 hours * 400e12 FLOP/s * 3600 s/hour ~= 9.2e24
alternatively:
6 * 70e9 * 15e12 = 6.3e24

So Llama 3 70B is a ~9e24 model.

Strength of Llama 3 400B

If the 400B model trains on the same dataset, we'd get up to ~4e25. This starts to really get up there. The Biden Executive Order had the reporting requirement set at 1e26, so this could be ~2X below that.

The only other point of comparison we'd have available is if you look at the alleged GPT-4 leaks, which have never been confirmed this would ~2X those numbers.

Now, there's a lot more that goes into the performance a model that doesn't fit on the napkin. E.g. data quality especially, but if you had to reduce a model to a single number, this is how you'd try, because it combines the size of the model with the length of training into a single "strength", of how many total FLOPs went into it.


RameshR
@rezmeram
For those curious about where the number 6 comes from in the estimate of llma strength from Llama itself:
The number 6 is a simplification, and it's not a hard and fast rule. It's based on the assumption that, on average, a model performs around 6 floating-point operations for each token it processes. This can vary depending on the specific architecture and implementation of the model.

The idea behind this estimate is that, for each token, the model might perform operations like:

1-2 operations to retrieve the token's embedding (a numerical representation of the token)
1-2 operations to perform self-attention (comparing the token to other tokens in the sequence)
1-2 operations to update the model's internal state


AmitP
@amitp_ai
·
4h
@karpathy
 a dumb question, but what is the rationale for 6 in 6ND? Thank

 
Unclecode (Hossein)
@unclecode
·
4h
For the 400B estimation, r u referring to the current checkout they shared in the report? 15 April version? Becoz 4e25 / (400e12 * 3600) will be around 27e6 hours.


Scott
@Scott_S612
·
8h
8B, 70B and 400B trained on same amount of tokens, does that mean the bigger ones could be significantly undertrained than the smaller ones?

