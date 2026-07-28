import { Message } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";
const MOCK_DELAY_MS = 800;

export async function sendMessage(
  message: string,
  history: Message[]
): Promise<Message> {
  if (USE_MOCK) return mockSendMessage(message);

  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed with status ${res.status}`);
  }

  return res.json();
}

async function mockSendMessage(message: string): Promise<Message> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));
  
  let content = "";
  if (message.includes("برد") || message.includes("أنفلونزا") || message.includes("فيلروس")) {
    content = `أهلاً بك! بالنسبة لاستفسارك حول نزلات البرد والفيروسات:\n\n1. **الراحة والتغذية:** يُوصى بأخذ قسط كافٍ من الراحة وشرب السوائل الدافئة مثل الزنجبيل والليمون.\n2. **المضادات الحيوية:** المضادات الحيوية تعالج البكتيريا فقط ولا تؤثر على الفيروسات المسببة للبرد.\n3. **الوقاية:** غسل اليدين باستمرار وتجنب مخالطة المصابين.\n\n*تنبيه: إذا استمرت الحرارة العالية لأكثر من 3 أيام، يُرجى مراجعة الطبيب.*`;
  } else if (message.includes("ضغط") || message.includes("قلب")) {
    content = `بالنسبة لصحة ضغط الدم والقلب:\n\n1. **التقليل من الصوديوم:** خفض نسبة الملح في الطعام.\n2. **الرياضة:** ممارسة المشي المنتظم لمدة 30 دقيقة يومياً.\n3. **المتابعة:** قياس ضغط الدم بانتظام وتسجيل القراءات.\n\n*يرجى استشارة طبيب الباطنية أو القلب لضبط جرعات الأدوية.*`;
  } else {
    content = `شكراً لاستفسارك حول: "${message}".\n\nإليك بعض النصائح الإرشادية العامة:\n• اتبع نظاماً غذائياً متوازناً غنياً بالمغذيات والماء.\n• احرص على ساعات نوم منتظمة (7-8 ساعات يومياً).\n• تجنب الإجهاد والتوتر وتناول العلاجات دون استشارة طبية.\n\nإذا كانت لديك أية أعراض خاصة، يُرجى استشارة الطبيب المختص.`;
  }

  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content,
  };
}