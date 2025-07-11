import requests
import logging

logger = logging.getLogger(__name__)

def send_slack_message(webhook_url: str, message: str) -> bool:
    """
    Slack 웹훅으로 메시지를 전송합니다.
    
    Args:
        webhook_url: Slack 웹훅 URL
        message: 전송할 메시지
        
    Returns:
        bool: 전송 성공 여부
    """
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Slack 메시지 전송 성공")
            return True
        else:
            logger.warning(f"Slack 메시지 전송 실패: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Slack 메시지 전송 중 네트워크 오류: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Slack 메시지 전송 중 예상치 못한 오류: {str(e)}")
        return False 