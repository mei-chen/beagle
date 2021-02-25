Agreement Type dataset
----------------------

This dataset is used to train the Agreement Type classifier, which classifies
between NDA, Commercial Agreement and other types of agreements.

The structure of this directory should look like this:

```
- .
  - nda
    - NDA_Sample1.txt
    - NDA_Sample2.txt
    - ...
  - agreement_type2
    - AgreementType2_Sample1.txt
    - AgreementType2_Sample2.txt
    - ...
  - other
    - Other_Sample1.txt
    - Other_Sample2.txt
    - ...
```

Each sample should be a plain text full agreement in `.txt` format. There's no
naming convention for the txt files themselves.

All samples in an `AgreementType` directory are positive samples for that type.
