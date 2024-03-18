from setuptools import setup, find_packages

setup(
    name='django_testcase_generator',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    description='A Django app to generate test cases from urls.py.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mohidul Hoque Arif',
    author_email='mohidulhoque216@gmail.com',
    url='https://github.com/arifbd2221/django_testcase_generator',
    license='MIT',
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='django, tests, unittest, django-rest-framework',
    install_requires=[
        'Django>=2.2',
        'djangorestframework',
    ],
)

