"""反检测脚本模块"""

from typing import Any


STEALTH_SCRIPT = """
// 隐藏webdriver属性
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 修改plugins数组，使其看起来像真实浏览器
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            {
                name: 'Chrome PDF Plugin',
                description: 'Portable Document Format',
                filename: 'internal-pdf-viewer',
                length: 1
            },
            {
                name: 'Chrome PDF Viewer',
                description: '',
                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                length: 1
            },
            {
                name: 'Native Client',
                description: '',
                filename: 'internal-nacl-plugin',
                length: 2
            }
        ];
        plugins.item = (index) => plugins[index] || null;
        plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
        plugins.refresh = () => {};
        return plugins;
    }
});

// 修改languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// 隐藏自动化标志
window.chrome = {
    runtime: {
        connect: function() {},
        sendMessage: function() {}
    },
    loadTimes: function() {},
    csi: function() {}
};

// 覆盖permissions查询
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// 隐藏自动化相关的属性
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;

// 修改navigator.platform
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});

// 修改navigator.hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8
});

// 修改navigator.deviceMemory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8
});

// 模拟真实的screen属性
Object.defineProperty(screen, 'width', {
    get: () => 1920
});
Object.defineProperty(screen, 'height', {
    get: () => 1080
});
Object.defineProperty(screen, 'availWidth', {
    get: () => 1920
});
Object.defineProperty(screen, 'availHeight', {
    get: () => 1040
});

// 模拟真实的canvas
const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' && this.width === 220 && this.height === 30) {
        // 可能是指纹检测，返回随机噪声
        return originalToDataURL.apply(this, arguments);
    }
    return originalToDataURL.apply(this, arguments);
};

// WebGL指纹混淆
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.apply(this, arguments);
};
"""


async def apply_stealth(context: Any) -> None:
    """应用反检测脚本到浏览器上下文

    Args:
        context: Playwright BrowserContext 对象
    """
    await context.add_init_script(STEALTH_SCRIPT)


async def apply_human_behavior(page: Any) -> None:
    """应用人类行为模拟

    Args:
        page: Playwright Page 对象
    """
    # 添加随机鼠标移动
    await page.evaluate("""
        const originalMouseMove = MouseEvent.prototype.constructor;
        window.humanMouseMove = function(x, y) {
            const event = new originalMouseMove('mousemove', {
                bubbles: true,
                cancelable: true,
                clientX: x + Math.random() * 10 - 5,
                clientY: y + Math.random() * 10 - 5
            });
            document.dispatchEvent(event);
        };
    """)