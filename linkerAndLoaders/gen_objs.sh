#! /bin/bash
rm -rf ./objs/
mkdir objs
python gen_obj.py ./objs/1.myobj
python gen_obj.py ./objs/2.myobj
python gen_obj.py ./objs/3.myobj
