# ERMiner
Python 3.9 implementation of algorithm ERMiner: Sequential Rule Mining using Equivalence Classes 
(from paper: https://www.philippe-fournier-viger.com/ERMiner_2014_sequential_rule_mining.pdf).
Supports SPMF data format.

### Instructions
To use ERMiner, run this command in the terminal:

`python main.py [-h] [-v] [-w] filename support confidence`

Positional arguments:
> filename - path to the file containing sequential database (in SPMF format)
  
> support - minimal support threshold in float format, eg: 0.5

> confidence - minimal confidence threshold in float format, eg: 0.75

Optional arguments:
> [-h, --help]  show help message and exit
  
> [-v, --verbose]  print detected rules
  
> [-w, --write]  write rules to `output.txt` file
