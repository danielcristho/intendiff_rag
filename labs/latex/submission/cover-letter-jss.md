# Draf cover letter — Journal of Systems and Software

Belum dikirim. Gunakan judul Inggris di bawah ketika naskah Inggris sudah selesai.
Target JSS mengikuti keputusan D109. Halaman editorial resmi mengembalikan
HTTP 403 pada pemeriksaan 19 Oktober 2026, sehingga nama editor tidak ditebak.
Alamatkan kepada editor yang ditunjuk sistem submission atau nama yang telah
dikonfirmasi pada halaman resmi sebelum pengiriman.

---

Dear Editors-in-Chief,

Please consider our manuscript, “IntentDiff-RAG: Package Intent and Reference
Examples for Malicious npm Update Detection with Local Language Models,” for
publication as a research article in the Journal of Systems and Software.

The study addresses a software maintenance decision: whether a dependency
update introduces malicious behavior and should be escalated for review.
This problem is relevant to software engineering readers concerned with
dependency management, software assurance, and the empirical evaluation of
AI-assisted development tools. Locally deployable language models offer an
alternative to external services, but their use requires evidence about both
missed attacks and the review burden caused by false alarms.

Our contribution is a controlled comparison of package intent and reference
example composition across six local, open-weight models and six input
configurations. We evaluate 129 source-labelled malicious updates and 1,868
typical updates, with campaign-aware uncertainty estimates. The comparison
between two malicious examples and one malicious plus one benign example
holds the number of examples and the identity and position of the primary
malicious example fixed. It measures the effect of replacing an example as a
whole, rather than attributing the effect to its label alone.

The results challenge the assumption that adding benign examples generally
reduces false alarms. False-positive rates increase on three models; the
clear decrease on Phi-4-mini accompanies reduced detection. Package intent
also has model-dependent effects. These findings provide evidence for
evaluating contextual assistance before adopting it in dependency review
workflows. We do not claim superiority over systems evaluated on different
datasets or readiness for autonomous blocking.

The manuscript reports source-label assumptions, data exclusions, model and
data expansion after initial results, invalid-output handling, and the limits
of the retrieval policy. A companion reproducibility document records the
frozen prompts, output schema, model revisions, and analysis inputs. Public
artifact access will be specified in the data availability statement before
submission.

Thank you for considering our manuscript.

Sincerely,

[Corresponding author]
[Affiliation]
[Email]

---

Sebelum dikirim, penulis harus mengisi identitas dan memverifikasi pernyataan
tentang persetujuan semua penulis, status pengiriman ke jurnal lain, publikasi
atau preprint terkait, konflik kepentingan, dan pendanaan. Pernyataan tersebut
tidak dibuat otomatis karena faktanya belum diberikan. Kesesuaian scope di
atas merupakan alasan pengajuan, bukan jaminan penerimaan editor.

Halaman resmi untuk pemeriksaan akhir:

- [Aims and scope](https://www.sciencedirect.com/journal/journal-of-systems-and-software/about/aims-and-scope)
- [Guide for authors](https://www.sciencedirect.com/journal/journal-of-systems-and-software/publish/guide-for-authors)
- [Editorial board](https://www.sciencedirect.com/journal/journal-of-systems-and-software/about/editorial-board)
