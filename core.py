import re
import discord
from discord.ext import commands

class SharksWaveInterpreter:
    def __init__(self, target_channel_id=None):
        self.variables = {}
        self.is_running = True
        self.bot = None  # .swe 내부에서 discord = command(...)를 만나면 생성됨
        self.target_channel_id = target_channel_id
        
        self.imports = {
            "import python and SWE.discord": False,
            "import discord.swe": False,
            "import bot": False
        }
        self.bot_framework_ready = False

    def execute_line(self, line: str):
        if not self.is_running:
            return None
            
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # 📡 [신규] .swe 전용 고유 봇 선언 파싱
        # 규격: discord = command(prefix:"🔑". it=값)
        if line.startswith("discord = command(") and line.endswith(")"):
            if not self.bot_framework_ready:
                return "❌ [SWE Runtime Error] discord = command를 정의하려면 상단 3개 패키지가 필수 임포트되어야 합니다."
            
            # 괄호 안의 매개변수 추출 (prefix:"!". it=it)
            inner_args = line[18:-1].strip()
            
            # 정규표현식으로 prefix와 it 값 쏙 빼내기
            match = re.search(r'prefix\s*:\s*"([^"]+)"\s*,\s*it\s*=\s*([a-zA-Z0-9_]+)', inner_args)
            if match:
                prefix_val, it_val = match.groups()
                
                # 가상 OS 환경에 맞춘 인텐트 기본 셋업
                intents = discord.Intents.default()
                intents.message_content = True
                
                # 내부 파이썬 봇 객체 동적 생성 및 바인딩 완료!
                self.bot = commands.Bot(command_prefix=prefix_val, intents=intents)
                return f"🤖 [SWE Kernel] 프리픽스 [{prefix_val}] 기반의 가상 디스코드 봇 객체가 활성화되었습니다."
            return "❌ [SWE Syntax Error] discord = command(prefix:\"!\". it=it) 형식을 확인하세요. (온점 대신 콤마 사용)"

        # (기존 sw.say, 변수 선언, say.discord 로직은 그대로 유지...)
