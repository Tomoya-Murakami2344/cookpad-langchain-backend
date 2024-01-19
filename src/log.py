import logging
from datetime import datetime
import os


def _create_log_config():
    """
    ログの設定

    ローカルファイルにログを出力する
    """

    # ログのフォーマット
    log_format = "%(asctime)s %(levelname)s %(name)s :%(message)s"
    # ログのレベル
    log_level = logging.INFO

    # ログのファイル名
    # ディレクトリの生成
    log_dirname = "log"
    os.makedirs(log_dirname, exist_ok=True)
    # ファイル名は実行日時にする
    now = datetime.now()
    log_filename = now.strftime("%Y%m%d") + ".log"
    # ファイルのパス
    log_filepath = os.path.join(log_dirname, log_filename)

    # ロガーの設定
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # ログのフォーマット
    formatter = logging.Formatter(log_format)

    # ログの出力先
    # ファイル
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 標準出力
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


my_logger = _create_log_config()