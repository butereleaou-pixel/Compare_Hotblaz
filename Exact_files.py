import json
import os
import re
import sys
import requests
import configparser
import subprocess
from datetime import datetime
from pathlib import Path
import time
import ast
from textwrap import dedent
import yaml
import sqlite3

def init_db(db_path="compare_50.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_samples(result, conn):
    cursor = conn.cursor()
    
    # 创建表（移除了 instance_id 字段）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT NOT NULL,
            answer TEXT
        )
    """)
    
    inserted_count = 0
    MAX_ROWS = 45  # 每次最多存储 45 行
    
    # 处理输入：无论是列表还是字符串，都转换为样本列表
    samples = []
    if isinstance(result, list):
        # 如果是列表，遍历每个元素并按 "compare_sample " 分割
        for item in result:
            if inserted_count >= MAX_ROWS:
                break
            # 对每个列表元素也进行分割
            split_samples = item.split("compare_sample ")
            # 添加前缀并过滤空样本
            for s in split_samples:
                if inserted_count >= MAX_ROWS:
                    break
                if s.strip():
                    samples.append("compare_sample " + s.strip())
    else:
        # 如果是字符串，直接分割
        raw_samples = result.split("compare_sample ")
        for s in raw_samples:
            if inserted_count >= MAX_ROWS:
                break
            if s.strip():
                samples.append("compare_sample " + s.strip())
    
    for full_sample in samples:
        if inserted_count >= MAX_ROWS:
            break

        if not full_sample.strip():
            continue
            
        if "[END]" in full_sample:
            try:
                cursor.execute(
                    "INSERT INTO sample (sample) VALUES (?)",
                    (full_sample.strip(),)
                )
                inserted_count += 1
            except Exception as e:
                print(f"Failed to insert: {e}")
                conn.rollback()
    
    conn.commit()
    print(f"✅ Successful insert {inserted_count} datas to db_path (limited to {MAX_ROWS})")
    # conn.close()


def store_pre_samples(result, conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pre_sample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT NOT NULL,
            answer TEXT,
            eucli_dis REAL,
            pick_ratio TEXT,
            mem_id INTEGER
        )
    """)

    inserted_count = 0
    MAX_ROWS = 30  # 每次最多存储 35 行

    for item in result:
        if inserted_count >= MAX_ROWS:
            break

        mem_id = item.get("mem_id")
        content = item.get("content")

        if content is None:
            continue

        if isinstance(content, list):
            flat_items = content
        else:
            flat_items = [content]

        for text_item in flat_items:
            if inserted_count >= MAX_ROWS:
                break

            split_samples = text_item.split("compare_sample ")
            samples = ["compare_sample " + s.strip() for s in split_samples if s.strip()]

            for full_sample in samples:
                if inserted_count >= MAX_ROWS:
                    break

                if "[END]" not in full_sample:
                    continue

                try:
                    cursor.execute(
                        "INSERT INTO pre_sample (sample, mem_id) VALUES (?, ?)",
                        (full_sample.strip(), mem_id)
                    )
                    inserted_count += 1
                except Exception as e:
                    print(f"Failed to insert: {e}")
                    conn.rollback()

    conn.commit()
    print(f"✅ Successfully inserted {inserted_count} rows (limited to {MAX_ROWS})")


if __name__ == "__main__":
    init_db(db_path="compare_50.db")


