import re
import asyncio
import discord
from discord.ext import commands

class SharksWaveInterpreter:
    def __init__(self, target_channel_id=None):
        self.variables = {}
        self.is_running = True
        self.bot = None
        self.target_channel_id = target_channel_id
        self.whale_task = None
        
        self.imports = {
            "import python and SWE.discord": False,
            "import discord.swe": False,
            "import bot": False
        }
        self.bot_framework_ready = False

    def check_imports(self, lines):
        for line in lines[:5]:
            line_strip = line.strip()
            if line_strip in self.imports:
                self.imports[line_strip] = True
                
        if all(self.imports.values()):
            self.bot_framework_ready = True
            print("외부 디스코드 API 연동 권한이 승인되었습니다.")

    async def start_60s_shutdown_timer(self):
        """60초가 지나면 외부 세션을 끊고 물리적으로 봇을 오프라인 시키는 타이머"""
        print("바깥 망 연결 시간 60초 카운트다운 개시.")
        await asyncio.sleep(60)
        
        if self.is_running:
            print("\n 60초 제한 시간에 도달했습니다. 외부 연결을 강제 차단합니다.")
            await self.force_stop_and_disconnect()

    def execute_line(self, line: str):
        if not self.is_running:
            return None
            
        line = line.strip()
        if not line or line.startswith("#"):
            return None
            
        if line.lower().startswith("sw.say(") and line.endswith(")"):
            content = line[7:-1].strip()
            if content.startswith('"') and content.endswith('"'): return content[1:-1]
            elif content in self.variables: return str(self.variables[content])
            return f"정의되지 않은 데이터: {content}"
            
        if line.startswith("discord = command(") and line.endswith(")"):
            if not self.bot_framework_ready:
                return "패키지 임포트가 누락되었습니다."
            
            inner_args = line[18:-1].strip()
            match = re.search(r'prefix\s*:\s*"([^"]+)"\s*,\s*it\s*=\s*([a-zA-Z0-9_]+)', inner_args)
            if match:
                prefix_val, _ = match.groups()
                intents = discord.Intents.default()
                intents.message_content = True
                
                self.bot = commands.Bot(command_prefix=prefix_val, intents=intents)
                
                @self.bot.event
                async def on_ready():
                    print(f"외부 통신망 도킹 성공: {self.bot.user.name} 가동 시작.")
                    if self.target_channel_id:
                        channel = self.bot.get_channel(self.target_channel_id)
                        if channel:
                            await channel.send("**Shark's Wave (.swe) Kernel Online** \n바깥 외부망과 성공적으로 연동되었습니다.")
                
                return f"[SWE Kernel] 프리픽스 [{prefix_val}] 봇 인스턴스 생성 완료."
        if line.lower().startswith("say.discord(") and line.endswith(")"):
            content = line[12:-1].strip()
            final_msg = content[1:-1] if (content.startswith('"') and content.endswith('"')) else self.variables.get(content, content)
            
            if self.bot and self.bot.is_ready() and self.target_channel_id:
                channel = self.bot.get_channel(self.target_channel_id)
                if channel:
                    self.bot.loop.create_task(channel.send(str(final_msg)))
            return f"바깥 채널로 송출: {final_msg}"

        if ": wave =" in line:
            match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*wave\s*=\s*(.*)", line)
            if match:
                var_name, var_value = match.groups()
                var_value = var_value.strip()
                if var_value.startswith('"') and var_value.endswith('"'): self.variables[var_name] = var_value[1:-1]
                elif var_value.isdigit(): self.variables[var_name] = int(var_value)
                else: self.variables[var_name] = var_value
                return None

        if line.lower().startswith("swe.login(") and line.endswith(")"):
            token_target = line[10:-1].strip()
            final_token = token_target[1:-1] if (token_target.startswith('"') or token_target.startswith("'")) else self.variables.get(token_target, "")
            
            if self.bot and final_token:
                asyncio.create_task(self.start_60s_shutdown_timer())
                asyncio.create_task(self.bot.start(final_token))
                return f"외부 인증 게이트웨이 개방. 토큰 접속 시도 중..."
            return "봇 인스턴스 또는 토큰이 유효하지 않습니다."

        return f"알 수 없는 명령: {line}"

    async def run_code(self, full_code: str):
        lines = full_code.split("\n")
        self.check_imports(lines)
        
        loop_body = []
        in_whale_block = False
        
        for line in lines:
            line_strip = line.strip()
            if line_strip in self.imports: continue

            if line_strip.startswith("Whale") and "{" in line_strip:
                in_whale_block = True
                continue
            
            if line_strip == "}" and in_whale_block:
                in_whale_block = False
                self.whale_task = asyncio.create_task(self._run_whale_loop(loop_body))
                continue

            if in_whale_block:
                loop_body.append(line)
            else:
                output = self.execute_line(line)
                if output: print(output)

    async def _run_whale_loop(self, loop_body):
        """Whale 무한루프가 외부 통신을 방해하지 않도록 별도 독립 가동하는 비동기 루프"""
        while self.is_running:
            for loop_line in loop_body:
                if not self.is_running: break
                output = self.execute_line(loop_line)
                if output: print(output)
            await asyncio.sleep(1)

    async def force_stop_and_disconnect(self):
        """외부 연결을 완전히 찢어버리고 세션을 파괴하는 절대 안전장치"""
        if not self.is_running: return

        self.is_running = False
        
        if self.whale_task:
            self.whale_task.cancel()
            
        if self.bot and not self.bot.is_closed():
