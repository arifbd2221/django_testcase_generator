# Django Testcase Generator

`django-testcase-generator` is a powerful tool for Django projects, designed to automatically generate test cases for views by analyzing URL configurations. Its goal is to speed up the initial setup of tests, providing developers with a solid foundation for building comprehensive test suites.

## Features

- **Automatic Test Generation**: Automatically creates test case boilerplates for both class-based views (CBVs) and function-based views (FBVs).
- **Customizable**: Flexible test template customization options to fit a variety of testing frameworks and preferences.
- **Ease of Use**: Simplifies the test creation process, making it accessible and straightforward for developers at any skill level.

## Installation

Install `django-testcase-generator` using pip by running the following command in your terminal:

```
pip install django-testcase-generator
```

**Ensure your virtual environment is activated when installing the package.**

## Configuration
After installation, include `django_testcase_generator` in the `INSTALLED_APPS` in your Django project's `settings.py`:

```
INSTALLED_APPS = [
    ...
    'django_testcase_generator',
    ...
]
```

Adding the package to INSTALLED_APPS activates the management commands provided by django-testcase-generator within your Django project.

## Usage
To generate test cases for a Django app, use the provided management command:
```
python manage.py generate_tests <app_name>
```

Replace <app_name> with the name of the app for which you are generating test cases. The command examines the urls.py of the specified app to produce the tests.