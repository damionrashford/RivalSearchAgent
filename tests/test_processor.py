import pytest
from src.reasoning.processor import ReasoningProcessor

@pytest.fixture
def processor():
    return ReasoningProcessor()

def test_process_step(processor):
    input_data = {
        'step_content': "Test step",
        'step_num': 1,
        'estimated_steps': 5,
        'continue_reasoning': True
    }
    response = processor.process_step(input_data)
    assert 'step_num' in response['content'][0]['text']
    assert len(processor.steps) == 1
