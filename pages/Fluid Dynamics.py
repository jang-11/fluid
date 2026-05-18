import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# 윈도우 한글 폰트 및 마이너스 기호 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 웹페이지 넓게 쓰기 설정
st.set_page_config(layout="wide", page_title="Flight Aerodynamics Lab")

st.title("🛩️ 에어포일 주변의 유동 변형 및 양·항력·양항비 해석 시뮬레이터")
st.markdown("날개 길이와 비행 매개변수를 조절하여 유선의 비틀림, 표면 압력, 그리고 비행 효율의 핵심인 '양항비'를 분석합니다.")

# ------------------------------------------------------------------
# 1. 사이드바 제어 변수
# ------------------------------------------------------------------
st.sidebar.header("⚙️ 비행 및 구조 매개변수")
air_speed = st.sidebar.slider("비행기 속도 ($v$, m/s)", 30, 150, 80, step=5)
wing_span = st.sidebar.slider("날개 길이 (b, m)", 5.0, 25.0, 15.0, step=0.5)
aoa = st.sidebar.slider("받음각 (AoA, °)", 0, 15, 6, step=1)

# ------------------------------------------------------------------
# 2. 공학적 데이터 및 압력(Pressure) 연산
# ------------------------------------------------------------------
rho = 1.225  # 대기 밀도 (kg/m^3, 해수면 기준)
chord = 2.0  # 날개 폭 (m)
wing_area = wing_span * chord  
aspect_ratio = (wing_span ** 2) / wing_area  

p_infinity = 101325  # 대기 정압 (Pa)
dynamic_pressure = 0.5 * rho * (air_speed ** 2)  # 동압

# 공기역학적 효율 계수 연산
Cl = 2 * np.pi * np.radians(aoa) * (aspect_ratio / (aspect_ratio + 2))
Cd_profile = 0.02  
Cd_induced = (Cl ** 2) / (np.pi * aspect_ratio)  
Cd = Cd_profile + Cd_induced

# 최종 순수 양항비 계산 (L/D = Cl / Cd)
lod_ratio = Cl / Cd if Cd > 0 else 0

# 실제 힘 계산 (kN 단위)
lift_force = dynamic_pressure * wing_area * Cl / 1000.0
drag_force = dynamic_pressure * wing_area * Cd / 1000.0

# 베르누이 정리를 적용한 날개 상/하부 평균 압력(Pa) 계산
p_lower = p_infinity + (dynamic_pressure * Cl * 0.4)
p_upper = p_infinity - (dynamic_pressure * Cl * 0.6)

# [상단 대시보드 수치 출력]
m1, m2, m3, m4 = st.columns(4)
m1.metric("비행기를 띄우는 힘 (양력)", f"{lift_force:.2f} kN")
m2.metric("공기가 뒤로 당기는 저항력 (항력)", f"{drag_force:.3f} kN")
m3.metric("날개 상·하부 압력차 ($\Delta P$)", f"{p_lower - p_upper:.1f} Pa")
m4.metric("🔥 현재 날개의 순수 양항비 ($L/D$)", f"{lod_ratio:.2f}")

# ------------------------------------------------------------------
# 3. 레이아웃 분할: [왼쪽 4 - 애니메이션] | [오른쪽 3 - 양력 계수 및 양항비 그래프]
# ------------------------------------------------------------------
col_vis, col_graph = st.columns([4, 3])

with col_vis:
    st.subheader("🍃 실시간 공기 유선 및 양·항력 가시화")
    
    html_code = f"""
    <div style="background: #ffffff; border-radius: 12px; padding: 10px; border: 1px solid #e2e8f0;">
        <canvas id="airfoilCanvas" width="750" height="430" style="width: 100%; background: #ffffff;"></canvas>
    </div>

    <script>
    const canvas = document.getElementById('airfoilCanvas');
    const ctx = canvas.getContext('2d');

    const speed = {air_speed};
    const span = {wing_span};
    const aoa = {aoa};
    const lift = {lift_force};
    const drag = {drag_force};
    
    const pUpper = Math.round({p_upper});
    const pLower = Math.round({p_lower});

    const wingX = 320;
    const wingY = 215;
    const wingLength = 210;
    const wingThickness = Math.max(18, 48 - (span * 1.0)); 

    const streams = [];
    const numLines = 15;
    for (let i = 0; i < numLines; i++) {{
        streams.push({{
            x: Math.random() * canvas.width,
            originalY: 40 + (i * 24),
            length: 60 + Math.random() * 30
        }});
    }}

    function drawAirfoil() {{
        ctx.save();
        ctx.translate(wingX, wingY);
        ctx.rotate(-aoa * Math.PI / 180);

        ctx.beginPath();
        ctx.moveTo(-wingLength/2, 0);
        ctx.bezierCurveTo(-wingLength/2, -wingThickness, wingLength/6, -wingThickness, wingLength/2, 0);
        ctx.bezierCurveTo(wingLength/6, wingThickness*0.2, -wingLength/3, wingThickness*0.2, -wingLength/2, 0);
        
        ctx.fillStyle = '#f1f5f9'; 
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = '#475569'; 
        ctx.stroke();
        
        ctx.restore();
    }}

    function getFlowY(currentX, originalY) {{
        let dx = currentX - wingX;
        let targetY = originalY;
        let distSq = (dx * dx) + (originalY - wingY) * (originalY - wingY) * 2.2;

        if (distSq < 150 * 150) {{
            let factor = Math.exp(-dx*dx / (2 * 90 * 90)); 
            if (originalY < wingY) {{
                targetY = originalY - (wingThickness * 0.85 + aoa * 2.2) * factor * (1 - Math.abs(originalY - wingY)/180);
            }} else {{
                targetY = originalY + (wingThickness * 0.35 + aoa * 1.0) * factor * (1 - Math.abs(originalY - wingY)/180);
            }}
        }}
        
        if (dx > 0) {{
            let downwashFactor = Math.min(1, dx / 300);
            let downwashAngle = (aoa * 2.4) * (15 / span); 
            targetY += downwashAngle * downwashFactor * Math.exp(-(originalY-wingY)*(originalY-wingY)/(180*180));
        }}
        return targetY;
    }}

    function drawArrow(startX, startY, len, angleDeg, color, label) {{
        let angleRad = angleDeg * Math.PI / 180;
        let targetX = startX + len * Math.cos(angleRad);
        let targetY = startY + len * Math.sin(angleRad);

        ctx.lineWidth = 3;
        ctx.strokeStyle = color;
        ctx.fillStyle = color;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(targetX, targetY);
        ctx.stroke();

        ctx.save();
        ctx.translate(targetX, targetY);
        ctx.rotate(angleRad + Math.PI / 2);
        ctx.beginPath();
        ctx.moveTo(-6, 8); ctx.lineTo(6, 8); ctx.lineTo(0, 0);
        ctx.fill();
        ctx.restore();

        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(label, targetX + (Math.cos(angleRad) * 12), targetY + (Math.sin(angleRad) * 12) + 4);
    }}

    function animate() {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        let bgGrad = ctx.createRadialGradient(wingX, wingY, 40, wingX, wingY, 350);
        bgGrad.addColorStop(0, 'rgba(14, 165, 233, 0.1)');
        bgGrad.addColorStop(1, '#ffffff');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.font = 'bold 13px sans-serif';
        ctx.fillStyle = '#0284c7'; 
        ctx.fillText("낮은 압력: " + pUpper.toLocaleString() + " Pa", wingX - 60, wingY - wingThickness - 45);
        ctx.fillStyle = '#ea580c'; 
        ctx.fillText("높은 압력: " + pLower.toLocaleString() + " Pa", wingX - 60, wingY + wingThickness + 55);

        streams.forEach(stream => {{
            let currentSpeed = speed * 0.05;
            if (stream.x > wingX - wingLength && stream.x < wingX + wingLength && stream.originalY < wingY) {{
                currentSpeed *= (1.22 + aoa * 0.01);
            }}

            ctx.beginPath();
            ctx.lineWidth = 1.6;
            ctx.strokeStyle = 'rgba(14, 165, 233, 0.7)'; 

            let startX = stream.x;
            let startY = getFlowY(startX, stream.originalY);
            ctx.moveTo(startX, startY);

            let segments = 5;
            let segWidth = stream.length / segments;
            for(let j = 1; j <= segments; j++) {{
                let nextX = startX + (j * segWidth);
                let nextY = getFlowY(nextX, stream.originalY);
                ctx.lineTo(nextX, nextY);
            }}
            ctx.stroke();

            if (Math.floor(stream.x) % 150 < 5) {{
                let midX = stream.x + stream.length/2;
                let midY = getFlowY(midX, stream.originalY);
                ctx.fillStyle = 'rgba(14, 165, 233, 0.9)';
                ctx.beginPath();
                ctx.moveTo(midX, midY - 3);
                ctx.lineTo(midX + 5, midY);
                ctx.lineTo(midX, midY + 3);
                ctx.fill();
            }}

            stream.x += currentSpeed;
            if (stream.x > canvas.width) stream.x = -stream.length;
        }});

        drawAirfoil();

        let liftArrowLen = Math.min(130, 35 + lift * 1.5);
        let dragArrowLen = Math.min(100, 25 + drag * 12.0);

        drawArrow(wingX, wingY - 5, liftArrowLen, -90 + aoa, '#db2777', "F 양력");
        drawArrow(wingX, wingY - 5, dragArrowLen, aoa, '#16a34a', "F 항력");

        requestAnimationFrame(animate);
    }}
    animate();
    </script>
    """
    components.html(html_code, height=450)

with col_graph:
    st.subheader("📊 비행 효율성(양항비) 실시간 정밀 분석")
    fig, ax = plt.subplots(2, 1, figsize=(6, 5.2), layout="tight")
    
    # 1번 그래프: 받들각 대비 순수 양력 효율 점수 곡선 (C_L)
    aoa_range = np.linspace(0, 15, 50)
    Cl_range = 2 * np.pi * np.radians(aoa_range) * (aspect_ratio / (aspect_ratio + 2))
    
    ax[0].plot(aoa_range, Cl_range, color='#0ea5e9', linewidth=2, label='양력 계수 ($C_L$)')
    ax[0].scatter([aoa], [Cl], color='#db2777', s=100, zorder=5, label='현재 상태')
    ax[0].set_title("받음각 대비 양력 효율 점수 곡선", fontsize=11, weight='bold', pad=8)
    ax[0].set_xlabel("받음각 (degree, °)", fontsize=9)
    ax[0].set_ylabel("양력 계수 ($C_L$)", fontsize=9)
    ax[0].set_xlim(-0.5, 20)
    ax[0].set_ylim(-0.1, 3)
    ax[0].grid(True, linestyle='--', alpha=0.5)
    ax[0].legend(fontsize=9, loc='upper left')
    
    # ------------------------------------------------------------------
    # [수정] 2번 그래프: 받들각 대비 최종 비행 효율성 '양항비(L/D)' 곡선
    # ------------------------------------------------------------------
    Cd_induced_range = (Cl_range ** 2) / (np.pi * aspect_ratio)
    Cd_total_range = Cd_profile + Cd_induced_range
    lod_range = Cl_range / Cd_total_range
    
    ax[1].plot(aoa_range, lod_range, color='#a855f7', linewidth=2, label='양항비 ($L/D$)')
    ax[1].scatter([aoa], [lod_ratio], color='#db2777', s=100, zorder=5, label='현재 효율')
    ax[1].set_title("받음각 대비 최종 비행 효율성 (양항비 곡선)", fontsize=11, weight='bold', pad=8)
    ax[1].set_xlabel("받음각 (degree, °)", fontsize=9)
    ax[1].set_ylabel("양항비 ($L/D$ Ratio)", fontsize=9)
    
    # 양항비 포물선 스케일을 위한 범위 고정
    ax[1].set_xlim(-0.5, 15.5)
    ax[1].set_ylim(-1, 25)
    ax[1].grid(True, linestyle='--', alpha=0.5)
    ax[1].legend(fontsize=9, loc='upper right')
    
    st.pyplot(fig)