#!/usr/bin/env python3
"""
Claude Code Prompt Enhancement Engine
Intelligently enhances vague prompts for better responses
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

class PromptEnhancer:
    def __init__(self):
        self.config_file = Path.home() / '.claude' / 'prompt-enhance-config.json'
        self.history_file = Path.home() / '.claude' / 'logs' / 'prompt-enhance-history.json'
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'enabled': True,
            'level': 'smart',  # 'smart', 'aggressive', 'minimal'
            'context_aware': True,
            'patterns': self._get_default_patterns()
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.config = {**default_config, **config}
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _get_default_patterns(self):
        """Get default enhancement patterns"""
        return {
            'vague_verbs': {
                'fix': 'debug and resolve',
                'improve': 'optimize and enhance',
                'check': 'analyze and validate',
                'update': 'modify and synchronize',
                'clean': 'refactor and organize'
            },
            'missing_context': {
                'this': 'the current file/issue',
                'it': 'the previously mentioned item',
                'that': 'the referenced element'
            },
            'specificity_triggers': [
                r'^make\s+(?!.*\s+(a|an|the))',  # "make better" -> needs object
                r'^add\s+(?!.*\s+(a|an|the))',   # "add feature" -> needs detail
                r'^create\s+(?!.*\s+(a|an|the))', # "create script" -> needs purpose
                r'^implement\s+(?!.*\s+(a|an|the))',
                r'^\w+\s+this$',  # Single verb + "this"
                r'^\w+\s+it$'     # Single verb + "it"
            ]
        }
    
    def enhance_prompt(self, prompt, context=None):
        """Enhance a prompt based on configuration"""
        if not self.config['enabled']:
            return prompt
            
        original = prompt
        enhanced = prompt
        
        # Get current directory context
        cwd = os.getcwd()
        project_context = self._get_project_context(cwd)
        
        # Apply enhancements based on level
        if self.config['level'] in ['smart', 'aggressive']:
            enhanced = self._apply_smart_enhancements(enhanced, project_context)
            
        if self.config['level'] == 'aggressive':
            enhanced = self._apply_aggressive_enhancements(enhanced)
        
        # Add context if missing
        if self.config['context_aware'] and project_context:
            enhanced = self._add_project_context(enhanced, project_context)
        
        # Log enhancement
        if enhanced != original:
            self._log_enhancement(original, enhanced)
            
        return enhanced
    
    def _get_project_context(self, path):
        """Determine project type from path"""
        path = Path(path)
        
        contexts = {
            'THESIS': {
                'type': 'academic',
                'language': 'LaTeX',
                'focus': 'research documentation'
            },
            'SEARXNG': {
                'type': 'search-engine',
                'language': 'Python',
                'focus': 'engine implementation'
            },
            'AI-TOOLS': {
                'type': 'machine-learning',
                'language': 'Python',
                'focus': 'AI/ML development'
            },
            'CONFIG': {
                'type': 'configuration',
                'language': 'Bash/JSON',
                'focus': 'system automation'
            }
        }
        
        for parent in path.parents:
            if parent.name in contexts:
                return contexts[parent.name]
        
        return None
    
    def _apply_smart_enhancements(self, prompt, context):
        """Apply intelligent enhancements"""
        enhanced = prompt
        
        # Check for vague patterns
        for pattern in self.config['patterns']['specificity_triggers']:
            if re.match(pattern, prompt, re.IGNORECASE):
                # Prompt is too vague
                enhanced = self._add_specificity(prompt, context)
                break
        
        # Replace vague verbs
        for vague, specific in self.config['patterns']['vague_verbs'].items():
            pattern = r'\b' + vague + r'\b'
            if re.search(pattern, enhanced, re.IGNORECASE):
                enhanced = re.sub(pattern, specific, enhanced, flags=re.IGNORECASE)
        
        # Fix ambiguous references
        for ambiguous, clear in self.config['patterns']['missing_context'].items():
            if ambiguous in enhanced.split() and len(enhanced.split()) < 5:
                enhanced = enhanced.replace(ambiguous, clear)
        
        return enhanced
    
    def _apply_aggressive_enhancements(self, prompt):
        """Apply more aggressive enhancements"""
        # Add action qualifiers
        action_qualifiers = {
            'create': 'create a well-structured',
            'write': 'write comprehensive',
            'implement': 'implement a robust',
            'add': 'add a complete',
            'build': 'build an efficient'
        }
        
        for action, qualified in action_qualifiers.items():
            if prompt.lower().startswith(action):
                prompt = prompt.replace(action, qualified, 1)
                
        return prompt
    
    def _add_specificity(self, prompt, context):
        """Add specificity to vague prompts"""
        if context:
            suffix = f" for this {context['type']} project"
            if not any(word in prompt.lower() for word in ['project', 'file', 'code']):
                prompt += suffix
                
        # Add file type hints
        if 'file' in prompt and not any(ext in prompt for ext in ['.py', '.js', '.md', '.txt']):
            if context and context['language'] == 'Python':
                prompt = prompt.replace('file', 'Python file')
                
        return prompt
    
    def _add_project_context(self, prompt, context):
        """Add project context if missing"""
        # Only add context for very short prompts
        if len(prompt.split()) < 5 and context:
            context_hints = {
                'academic': ' (in LaTeX format)',
                'search-engine': ' (following SearXNG patterns)',
                'machine-learning': ' (with proper ML conventions)',
                'configuration': ' (with error handling)'
            }
            
            hint = context_hints.get(context['type'], '')
            if hint and hint.strip('() ') not in prompt:
                prompt += hint
                
        return prompt
    
    def _log_enhancement(self, original, enhanced):
        """Log prompt enhancements"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'enhanced': enhanced,
            'level': self.config['level'],
            'cwd': os.getcwd()
        }
        
        history = []
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        
        history.append(entry)
        
        # Keep last 100 entries
        history = history[-100:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def toggle(self, state=None):
        """Toggle enhancement on/off"""
        if state is None:
            self.config['enabled'] = not self.config['enabled']
        else:
            self.config['enabled'] = state.lower() in ['on', 'true', '1', 'yes']
        
        self.save_config()
        return self.config['enabled']
    
    def set_level(self, level):
        """Set enhancement level"""
        valid_levels = ['smart', 'aggressive', 'minimal']
        if level in valid_levels:
            self.config['level'] = level
            self.save_config()
            return True
        return False
    
    def get_status(self):
        """Get current status"""
        return {
            'enabled': self.config['enabled'],
            'level': self.config['level'],
            'context_aware': self.config['context_aware']
        }

if __name__ == '__main__':
    import sys
    
    enhancer = PromptEnhancer()
    
    if len(sys.argv) < 2:
        print(json.dumps(enhancer.get_status(), indent=2))
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'enhance':
        if len(sys.argv) < 3:
            print("Usage: prompt-enhancer.py enhance \"your prompt\"")
            sys.exit(1)
        prompt = ' '.join(sys.argv[2:])
        enhanced = enhancer.enhance_prompt(prompt)
        print(enhanced)
        
    elif command == 'toggle':
        state = sys.argv[2] if len(sys.argv) > 2 else None
        enabled = enhancer.toggle(state)
        print(f"Prompt enhancement: {'ON' if enabled else 'OFF'}")
        
    elif command == 'level':
        if len(sys.argv) < 3:
            print(f"Current level: {enhancer.config['level']}")
        else:
            if enhancer.set_level(sys.argv[2]):
                print(f"Level set to: {sys.argv[2]}")
            else:
                print("Invalid level. Use: smart, aggressive, or minimal")
                
    elif command == 'status':
        print(json.dumps(enhancer.get_status(), indent=2))
        
    elif command == 'history':
        if enhancer.history_file.exists():
            with open(enhancer.history_file, 'r') as f:
                history = json.load(f)
                for entry in history[-10:]:  # Last 10
                    print(f"\n[{entry['timestamp']}]")
                    print(f"Original: {entry['original']}")
                    print(f"Enhanced: {entry['enhanced']}")