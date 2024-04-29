#!/usr/bin/env python
# coding: utf-8

# In[1]:


def input_student(student) :
    student['name'] = input('Name : ')
    student['kor'] = int(input('Korean : '))
    student['eng'] = int(input('English : '))
    student['math'] = int(input('Math : '))    
