# Data Format

Dokumen ini menjelaskan **format standar dataset** yang digunakan dalam `llm-data-pipeline` untuk mendukung training model LLM (misalnya SFT & DPO).

## Struktur Dataset

Setiap record dalam dataset mengikuti format JSON:

```json
{
  "instruction": "Tulis ringkasan singkat dari teks berikut.",
  "input": "Artificial Intelligence (AI) adalah bidang ilmu komputer...",
  "output": "AI adalah cabang ilmu komputer yang mempelajari pembuatan sistem cerdas."
}
```

### Penjelasan Field

* **instruction** → Instruksi atau perintah untuk model.
* **input** → (Opsional) Data tambahan sebagai konteks.
* **output** → Jawaban/target yang benar.

---

## Aturan Format

1. **Encoding** → Semua file harus UTF-8.
2. **Panjang teks** →

   * Instruction ≤ 512 karakter.
   * Input ≤ 2000 karakter.
   * Output ≤ 2000 karakter.
3. **Consistency** → Semua record harus memiliki `instruction` & `output`. Field `input` opsional.
4. **Data Split** →

   * Train: 80%
   * Validation: 10%
   * Test: 10%

---

## Contoh Data Split

```json
{
  "train": [ {record1}, {record2}, ... ],
  "validation": [ {recordX}, {recordY}, ... ],
  "test": [ {recordM}, {recordN}, ... ]
}
```

---

## Catatan

* Format ini kompatibel dengan banyak framework LLM fine-tuning (misalnya HuggingFace `transformers`, OpenAI `fine-tuning`).
* Jika ada field tambahan (misalnya metadata), pastikan tidak mengganggu struktur utama.
