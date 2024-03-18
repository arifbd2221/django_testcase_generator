# generate_tests.py
import re
from rest_framework import serializers
from django.urls import resolve, Resolver404
from django.urls import URLPattern, URLResolver
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Generates test cases for views based on serializers in a specified Django app'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='The Django app name to generate tests for')
    
    def load_urlconf_module(self, urlconf_module):
        # Import the module where urlpatterns is defined
        if isinstance(urlconf_module, str):
            return __import__(urlconf_module, fromlist=['urlpatterns'])
        return urlconf_module

    def extract_url_patterns(self, urlpatterns, prefix='', namespace=None):
        # Recursively extract URL patterns from urlpatterns
        extracted_patterns = []
        for pattern in urlpatterns:
            current_namespace = namespace
            if isinstance(pattern, URLResolver):
                if pattern.namespace:
                    current_namespace = pattern.namespace
                extracted_patterns.extend(
                    self.extract_url_patterns(pattern.url_patterns, prefix=prefix + pattern.pattern.describe(), namespace=current_namespace)
                )
            elif isinstance(pattern, URLPattern):
                # Direct URLPattern, extract pattern and view
                try:
                    if hasattr(pattern.callback, 'view_class'):
                        view = pattern.callback.view_class
                    else:
                        view = pattern.callback
                    pattern_str = prefix + pattern.pattern.describe()
                    url_name = pattern.name
                    extracted_patterns.append((pattern_str, view, url_name, current_namespace))
                except Exception as e:
                    continue
                
        return extracted_patterns

    def parse_urls_py(self, app_name):
        urlconf_module = self.load_urlconf_module(app_name + '.urls')
        urlpatterns = getattr(urlconf_module, 'urlpatterns', [])
        return self.extract_url_patterns(urlpatterns)
    
    def get_view_from_url(self, pattern):
        try:
            return resolve(pattern).func
        except Resolver404:
            return None

    def get_serializer_from_view(self, view):
        # This function needs to dynamically import the view and attempt to find a serializer
        serializer_class = None
        if hasattr(view, 'get_serializer_class'):
            serializer_class = view.serializer_class
        elif hasattr(view, 'serializer_class'):
            serializer_class = view.serializer_class
        # Add more checks as needed
        return serializer_class
    
    
    def write_test_case_to_file(self, app_name, test_case_content):
        # Determine the directory for the tests within the app
        app_tests_dir = os.path.join(settings.BASE_DIR, app_name, 'tests')
        
        # Ensure the tests directory exists
        if not os.path.exists(app_tests_dir):
            os.makedirs(app_tests_dir)

        # Path for the test file
        test_file_path = os.path.join(app_tests_dir, 'test_generated_api.py')
        
        # Check if we're writing to the file for the first time to include imports
        first_write = not os.path.exists(test_file_path)

        # Write or append the test case content to the file
        with open(test_file_path, 'a' if not first_write else 'w') as file:
            # If it's the first write, prepend necessary imports
            if first_write:
                file.write("from django.test import TestCase\nfrom django.urls import reverse\nfrom rest_framework import status\n\n")
            file.write(test_case_content)
    
    def get_supported_http_methods(self, view):
        if hasattr(view, 'as_view'):
            # Handling class-based views
            view_class = view
            http_methods = []
            for method in ['get', 'post', 'put', 'patch', 'delete']:
                if hasattr(view_class, method):
                    http_methods.append(method.upper())
            return http_methods
        # Add logic for function-based views if necessary
        # This could be based on documentation, naming conventions, or decorators
        return ['GET']  # Default assumption, adjust as needed
    
    
    def generate_dynamic_data(self, serializer_class):
        """
        Generates a dictionary of example data for the given serializer.
        This is a basic implementation and might need to be adjusted based on field types.
        """
        example_data = {}
        for field_name, field in serializer_class().get_fields().items():
            if field.read_only:
                continue  # Skip read-only fields
            # Example simple mapping, extend this based on your needs
            if isinstance(field, serializers.CharField):
                example_data[field_name] = 'example'
            elif isinstance(field, serializers.IntegerField):
                example_data[field_name] = 1
            elif isinstance(field, serializers.BooleanField):
                example_data[field_name] = True
            # Add more field types as necessary
        
        return example_data
    
    
    def generate_placeholders_from_pattern(self, pattern):
        # A simple mapping from URL pattern types to example values
        type_to_example = {
            'str': 'example_string',
            'int': '1',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
            # Add more mappings as necessary for different types
        }
        
        # Find all named groups in the pattern (e.g., '<str:app_slug>')
        named_groups = re.findall(r'<(\w+):(\w+)>', pattern)
        
        placeholders = {}
        for type_hint, name in named_groups:
            # Use the type hint to generate an example value, defaulting to 'example' if not found
            example_value = type_to_example.get(type_hint, 'example')
            placeholders[name] = example_value
        
        return placeholders
    

    def generate_serializer_test_case(self, serializer_class, app_name, pattern, url_name, namespace, http_methods):
        test_cases_content = ""
        placeholders = self.generate_placeholders_from_pattern(pattern)
        kwargs_str = ', '.join(f"'{k}':'{v}'" for k, v in placeholders.items())
        reverse_call = f"reverse('{app_name}:{url_name}', kwargs={{{kwargs_str}}})"
        example_data = self.generate_dynamic_data(serializer_class)
        
        for method in http_methods:
            method_lower = method.lower()
            test_method_name = f"test_{method_lower}_valid_data"
            data_line = f"data={example_data}" if example_data else ""
            response_line = f"response = self.client.{method_lower}(url, {data_line}, format='json')" if data_line else f"response = self.client.{method_lower}(url)"
            status_check = "status.HTTP_201_CREATED" if method == 'POST' else "status.HTTP_200_OK"
            
            test_case_content = f"""
class {serializer_class.__name__}{method}TestCase(TestCase):
    def {test_method_name}(self):
        url = {reverse_call}
        {response_line}
        self.assertEqual(response.status_code, {status_check})
        # Add more assertions based on method
        """
            test_cases_content += test_case_content
        # Write the generated test case to the appropriate file
        self.write_test_case_to_file(app_name, test_case_content)


    def handle(self, *args, **options):
        app_name = options['app_name']
        self.stdout.write(self.style.SUCCESS(f'Generating tests for app: {app_name}'))
        
        # Placeholder for logic to locate the app's urls.py and generate tests
        app_path = os.path.join(settings.BASE_DIR, app_name)
        urls_py_path = os.path.join(app_path, 'urls.py')

        if not os.path.exists(urls_py_path):
            raise CommandError(f'{app_name}/urls.py does not exist.')
        
        self.stdout.write(self.style.SUCCESS(f'Found urls.py for {app_name}'))
        
        url_patterns = self.parse_urls_py(app_name)
        for pattern, view, url_name, namespace in url_patterns:
            serializer_class = self.get_serializer_from_view(view)
            if serializer_class:
                http_method = self.get_supported_http_methods(view)
                self.generate_serializer_test_case(
                    serializer_class, 
                    app_name, 
                    pattern, 
                    url_name, 
                    namespace,
                    http_method,
                )
