import logging

def configure_logging():
    # 配置主應用程序的基本日誌
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='app.log',
                        filemode='a')

    # 創建一個專門處理消息日誌的 Logger
    message_logger = logging.getLogger('MessageLogger')
    message_handler = logging.FileHandler('message.log')
    message_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    message_handler.setFormatter(message_formatter)
    message_logger.addHandler(message_handler)
    message_logger.setLevel(logging.INFO)

    # 創建一個專門處理時間日誌的 Logger
    time_logger = logging.getLogger('TimeLogger')
    time_handler = logging.FileHandler('time.log')
    time_formatter = logging.Formatter('%(asctime)s - %(message)s')
    time_handler.setFormatter(time_formatter)
    time_logger.addHandler(time_handler)
    time_logger.setLevel(logging.INFO)

    # 添加控制台輸出，方便在控制台查看日誌
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    # logging.getLogger().addHandler(console_handler)
