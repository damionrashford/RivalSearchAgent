import os
import json
from typing import Dict, List

class ReasoningProcessor:
    def __init__(self):
        self.steps: List[Dict] = []
        self.alternate_paths: Dict[str, List[Dict]] = {}
        self.suppress_logs = os.environ.get('SUPPRESS_LOGS', 'false').lower() == 'true'

    def process_step(self, input_data: Dict) -> Dict:
        required = ['step_content', 'step_num', 'estimated_steps', 'continue_reasoning']
        for key in required:
            if key not in input_data:
                raise ValueError(f"Missing {key}")
        step = {
            'step_content': str(input_data['step_content']),
            'step_num': int(input_data['step_num']),
            'estimated_steps': int(input_data['estimated_steps']),
            'continue_reasoning': bool(input_data['continue_reasoning']),
            'is_revision': bool(input_data.get('is_revision', False)),
            'revises_step': int(input_data['revises_step']) if 'revises_step' in input_data else None,
            'branch_from_step': int(input_data['branch_from_step']) if 'branch_from_step' in input_data else None,
            'branch_id': str(input_data['branch_id']) if 'branch_id' in input_data else None,
            'needs_more_steps': bool(input_data.get('needs_more_steps', False)),
        }
        self.steps.append(step)
        if step['branch_from_step'] and step['branch_id']:
            self.alternate_paths.setdefault(step['branch_id'], []).append(step)
        if not self.suppress_logs:
            prefix = "Revision" if step['is_revision'] else "Step"
            context = f" (revising {step['revises_step']})" if step['is_revision'] else f" (branch {step['branch_id']} from {step['branch_from_step']})" if step['branch_from_step'] else ""
            print(f"{prefix} {step['step_num']}/{step['estimated_steps']}{context}: {step['step_content']}")
        response = {
            'step_num': step['step_num'],
            'estimated_steps': step['estimated_steps'],
            'continue_reasoning': step['continue_reasoning'],
            'paths': list(self.alternate_paths.keys()),
            'steps_count': len(self.steps)
        }
        return {'content': [{'type': 'text', 'text': json.dumps(response, indent=2)}]}
