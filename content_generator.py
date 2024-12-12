import json

class ContentGenerator:
    def __init__(self, raw_content):
        self.raw_content = raw_content
        self.sections = []

    def process_content(self):
        # Split the raw content into sections based on some logic
        # For this example, we'll split by line breaks and filter out empty lines
        lines = self.raw_content.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if line:
                if current_section is None:
                    current_section = {'title': 'Aspectos Adicionales', 'content': []}
                current_section['content'].append(line)
            else:
                if current_section:
                    self.sections.append(current_section)
                    current_section = None

        if current_section:
            self.sections.append(current_section)  # Add the last section if exists

    def to_json(self):
        return json.dumps(self.sections, ensure_ascii=False, indent=4)

# Example usage:
# generator = ContentGenerator(raw_content)
# generator.process_content()
# json_output = generator.to_json()
