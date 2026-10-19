# English submission front matter

Draft accompanying the Indonesian manuscript; the manuscript body has not
been translated. Numerical claims use the same analysis as the manuscript.

## Title

IntentDiff-RAG: Package Intent and Reference Examples for Malicious npm Update Detection with Local Language Models

## Abstract

Dependency updates can introduce malicious code that resembles legitimate
software behavior. This study evaluates whether package intent and reference
examples help local language models detect malicious updates while limiting
false alarms. Six input configurations are compared across six open-weight
models with 3–8 billion parameters, using 129 source-labelled malicious
updates from 98 campaign clusters and 1,868 typical updates assumed benign
after advisory screening. Paired comparisons control example count and the
identity and position of the primary malicious example; uncertainty is
estimated by campaign-level bootstrapping. Without examples, detection rates
range from 42.64% to 79.07% and false-positive rates from 6.37% to 65.15%
across models. Replacing one of two malicious examples with a benign example
increases Qwen3-4B detection by 8.53 percentage points and false positives by
2.30 points. For Phi-4-mini, the same replacement reduces false positives by
5.46 points but reduces detection by 8.53 points. Package intent lowers false
positives on three models without a clear change in detection, while
increasing both rates on two others. The study provides empirical evidence
that the benefits of intent and example composition depend on the model and
retrieval conditions. The results do not support direct deployment for
autonomous blocking and motivate joint evaluation of detection and false
alarms before adopting contextual assistance in dependency review.

## Keywords

malicious package updates; npm; retrieval-augmented generation; open-weight language models; false positives

## Author review

Review terminology and the final English manuscript together before submission.
Do not present this front matter as a complete English manuscript.
