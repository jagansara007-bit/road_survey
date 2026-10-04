# Dataset Audit Report

**Policy:** `--excluded-only-policy drop`  
**Note:** Real-data numbers are NOT MEASURED (no dataset present at run time). This report reflects synthetic / provided dataset only.

## Split: `train`

| Metric | Count |
|:-------|------:|
| Total images | 40 |
| Images with no label file | 0 |
| Images with empty label file | 2 |
| Excluded-only images | 4 |

### Boxes per class ID

| Class ID | Count |
|:---------|------:|
| D00 | 34 |
| D10 | 11 |
| D20 | 18 |
| D40 | 9 |
| D44 | 10 |

### Excluded-only images (policy=`drop`)

| Filename |
|:---------|
| `Japan_seq01_0000.jpg` |
| `Japan_seq01_0001.jpg` |
| `Japan_seq01_0002.jpg` |
| `Japan_seq01_0003.jpg` |

## Split: `val`

| Metric | Count |
|:-------|------:|
| Total images | 15 |
| Images with no label file | 0 |
| Images with empty label file | 0 |
| Excluded-only images | 0 |

### Boxes per class ID

| Class ID | Count |
|:---------|------:|
| D00 | 15 |
| D10 | 5 |
| D20 | 8 |
| D40 | 4 |
| D44 | 3 |

## Split: `test`

| Metric | Count |
|:-------|------:|
| Total images | 25 |
| Images with no label file | 0 |
| Images with empty label file | 2 |
| Excluded-only images | 4 |

### Boxes per class ID

| Class ID | Count |
|:---------|------:|
| D00 | 19 |
| D10 | 6 |
| D20 | 10 |
| D40 | 5 |
| D44 | 7 |

### Excluded-only images (policy=`drop`)

| Filename |
|:---------|
| `Japan_seq02_0000.jpg` |
| `Japan_seq02_0001.jpg` |
| `Japan_seq02_0002.jpg` |
| `Japan_seq02_0003.jpg` |
