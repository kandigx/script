from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
import asyncio
import csv
from datetime import datetime
import os
import requests
import zipfile
from io import BytesIO
import time

class GameScraper:
    def __init__(self):
        print("初始化爬虫...")
        self.setup_driver()
        self.csv_file = 'games_data.csv'
        self.init_csv()
        
    def setup_driver(self):
        """初始化或重新初始化WebDriver"""
        chrome_options = Options()
        
        # 添加更多的选项来处理SSL问题
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--reduce-security-for-testing')
        
        # 禁用日志输出
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 设置日志级别
        chrome_options.add_argument('--log-level=3')  # 仅显示致命错误
        
        driver_path = os.path.join("chromedriver", "chromedriver-win64", "chromedriver.exe")
        
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
            
            self.driver = webdriver.Chrome(
                service=Service(driver_path),
                options=chrome_options
            )
            print("Chrome驱动初始化成功！")
        except Exception as e:
            print(f"Chrome驱动初始化失败: {str(e)}")
            raise

    def init_csv(self):
        """初始化CSV文件"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'game_name',
                    'game_url',
                    'iframe_src',
                    'iframe_id',
                    'iframe_class',
                    'timestamp'
                ])
                writer.writeheader()
    
    def save_to_csv(self, game_data):
        """保存数据到CSV文件"""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=game_data.keys())
            writer.writerow(game_data)
    
    async def get_game_links(self):
        """获取所有游戏链接"""
        print("正在访问网站首页...")
        self.driver.get("https://www.onlinegames.io/")
        await asyncio.sleep(3)
        
        print("正在获取游戏链接...")
        try:
            # 使用XPath排除侧边栏的链接，只获取主内容区域的游戏链接
            game_elements = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(@href, 'onlinegames.io/') and not(ancestor::nav[@class='sidebar']) and not(contains(@href, '/t/')) and not(@href='https://www.onlinegames.io/')]"
            )
            
            games = []
            for elem in game_elements:
                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()
                    
                    # 验证链接格式并排除特定路径
                    if (href 
                        and text 
                        and href.startswith('https://www.onlinegames.io/') 
                        and not any(x in href.lower() for x in ['/t/', '/tag/', '/about/', '/contact/', '/privacy-policy/'])):
                        
                        # 确保链接指向具体游戏页面
                        parts = href.strip('/').split('/')
                        if len(parts) == 4:  # 格式应该是: https://www.onlinegames.io/game-name/
                            print(f"找到游戏: {text} -> {href}")
                            games.append((text, href))
                        else:
                            print(f"跳过非游戏链接: {href}")
                            
                except Exception as e:
                    print(f"处理元素时出错: {str(e)}")
                    continue
            
            # 去重并排序
            games = list(set(games))
            games.sort(key=lambda x: x[0])
            
            print(f"\n总共找到 {len(games)} 个唯一游戏链接")
            
            # 打印所有找到的游戏
            if games:
                print("\n找到的游戏列表:")
                for idx, (name, url) in enumerate(games, 1):
                    print(f"{idx}. {name} ({url})")
            else:
                print("没有找到任何游戏链接！")
            
            return games
            
        except Exception as e:
            print(f"获取游戏链接时出错: {str(e)}")
            return []

    async def extract_game_iframe(self, game_name, url):
        """提取单个游戏页面的iframe信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\n正在处理游戏: {game_name} (尝试 {attempt + 1}/{max_retries})")
                print(f"访问URL: {url}")
                
                # 跳过随机游戏页面
                if 'random' in url.lower():
                    print("跳过随机游戏页面")
                    return
                
                # 检查会话是否有效，如果无效则重新初始化
                try:
                    self.driver.current_url
                except (WebDriverException, SessionNotCreatedException):
                    print("会话已失效，重新初始化驱动...")
                    self.setup_driver()
                
                self.driver.get(url)
                await asyncio.sleep(3)
                
                # 查找游戏iframe
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                
                if iframes:
                    print(f"找到 {len(iframes)} 个iframe")
                    for idx, iframe in enumerate(iframes):
                        src = iframe.get_attribute("src")
                        if not src:
                            continue
                        
                        game_data = {
                            "game_name": game_name,
                            "game_url": url,
                            "iframe_src": src,
                            "iframe_id": iframe.get_attribute("id") or f"iframe_{idx}",
                            "iframe_class": iframe.get_attribute("class") or "无class",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        self.save_to_csv(game_data)
                        print(f"✓ 成功保存 {game_name} 的iframe信息")
                        return  # 成功处理后退出
                else:
                    print(f"⚠ 警告: 在 {game_name} 中没有找到iframe")
                    
                break  # 如果没有发生异常，跳出重试循环
                
            except Exception as e:
                print(f"✗ 处理出错 (尝试 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    print("等待后重试...")
                    await asyncio.sleep(2)
                    continue
                print(f"放弃处理 {game_name} 经过 {max_retries} 次尝试")

    async def process_all_games(self):
        """处理所有游戏"""
        game_info = await self.get_game_links()
        
        for index, (game_name, url) in enumerate(game_info, 1):
            print(f"\n处理进度: {index}/{len(game_info)}")
            await self.extract_game_iframe(game_name, url)
            await asyncio.sleep(1)  # 添加间隔，避免请求过快
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            self.driver.quit()

async def main():
    print("=== 游戏爬虫启动 ===")
    scraper = GameScraper()
    try:
        await scraper.process_all_games()
    finally:
        scraper.cleanup()
    print("\n=== 爬虫运行完成！===")
    print(f"数据已保存到: {os.path.abspath(scraper.csv_file)}")

if __name__ == "__main__":
    asyncio.run(main())