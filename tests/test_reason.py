import pytest
from src.reasoning.processor import ReasoningProcessor

def test_reasoning_processor():
    """Test the core reasoning processor functionality."""
    processor = ReasoningProcessor()
    
    test_input = {
        "step_content": "test reasoning step", 
        "step_num": 1, 
        "estimated_steps": 3, 
        "continue_reasoning": True
    }
    
    response = processor.process_step(test_input)
    assert 'content' in response
    assert isinstance(response['content'], list)
    assert len(response['content']) > 0
    assert 'text' in response['content'][0]
