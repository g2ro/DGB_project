#!/usr/bin/env python
# coding: utf-8

# In[5]:


def output_student(student): 
    print('이름 = ', student['name'], end='  ')
    print('국어 = ', student['kor'], end='  ')
    print('영어 = ', student['eng'], end='  ')
    print('수학 = ', student['math'], end='  ')
    print('총점 = ', student['tot'], end='  ')
    print('평균 = ', student['avg'], end='  ')
    print('성적 = ', student['grade'])
