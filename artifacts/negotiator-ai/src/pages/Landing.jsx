// Главная страница (лендинг) для гостей и вошедших пользователей.
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, ChevronDown, ShieldCheck, X } from 'lucide-react';
import { categories, categoryLabel } from '@/data/categories';
import { scenariosApi } from '@/lib/api';
import logo from '../assets/logo.png';

const faqItems = [
  {
    q: 'Это настоящий разговор с человеком?',
    a: 'Нет, в симуляции вы говорите голосом, а AI-собеседник отвечает вам текстом. Он реагирует на ваши аргументы и меняет тактику по ходу диалога.',
  },
  {
    q: 'Нужно ли включать камеру?',
    a: 'Нет, камера не нужна. Понадобится только микрофон — важны содержание и формулировки, а не внешний вид.',
  },
  {
    q: 'Что произойдёт с моими записями?',
    a: 'Транскрипт сохраняется в вашем профиле и виден только вам — через историю сессий.',
  },
  {
    q: 'Сколько длится одна тренировка?',
    a: 'Обычно 5–10 минут вместе с брифингом и разбором результатов.',
  },
];

export default function Landing({ user }) {
  const [, navigate] = useLocation();
  const [openCase, setOpenCase] = useState(null);
  const [openFaq, setOpenFaq] = useState(0);
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    scenariosApi.list().then((list) => setFeatured(list.slice(0, 3))).catch(() => setFeatured([]));
  }, []);

  const openCatalog = () => navigate(user ? '/catalog' : '/register');
  const openCaseInConstructor = (id) => navigate(user ? `/constructor?case=${id}` : '/register');

  return (
    <main>
      <section className="hero container-wide">
        <div className="hero-grid">
          <div>
            <span className="eyebrow">Тренажёр сложных разговоров</span>
            <p className="hero-slogan">
              <span>Speak</span> Fastur
            </p>
            <p className="hero-copy">Fastur помогает найти точные слова до того, как разговор начнётся. Практикуйте деловые сценарии с AI, отвечая голосом, и получайте разбор, которому можно доверять.</p>
            <div className="hero-actions">
              <button className="btn btn-primary" onClick={openCatalog} data-testid="button-hero-start">
                Начать тренировку <ArrowRight size={16} />
              </button>
              <a href="#method" className="btn btn-quiet" data-testid="link-hero-method">Посмотреть подход</a>
            </div>
            <div className="hero-note">
              <ShieldCheck size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />
              Без оценок личности. Только конкретные навыки.
            </div>
          </div>
          <div className="arena-visual">
            <div className="orb orb-two" />
            <div className="orb orb-one" />
            <div className="arena-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="eyebrow">СЕЙЧАС В АРЕНЕ</span>
                <span className="status-dot" />
              </div>
              <h3>{featured[0]?.name || 'Обсуждение повышения'}</h3>
              <p className="muted" style={{ fontSize: 12, margin: '0 0 18px' }}>
                Категория · {categoryLabel(featured[0]?.category) || 'Общение с руководством'}
              </p>
              <div className="mini-row"><span>Цель разговора</span><strong>Конкретика</strong></div>
              <div className="mini-row"><span>Ваша стратегия</span><strong>BATNA</strong></div>
              <div className="mini-row"><span>Готовность</span><strong style={{ color: '#9de3e5' }}>78%</strong></div>
            </div>
          </div>
        </div>
      </section>

      <section id="method" className="section container-wide">
        <div className="section-heading">
          <span className="eyebrow">Метод</span>
          <h2 className="display">Три шага до разговора, в котором вы уверены.</h2>
          <p className="muted">Не теория ради теории. Короткая практика, наблюдение и следующий точный шаг.</p>
        </div>
        <div className="steps-grid">
          <article className="card step-card">
            <span className="step-no">01 / НАСТРОЙКА</span>
            <h3>Выберите ситуацию</h3>
            <p className="muted">Категория, кейс и сложность — чтобы тренировка была про вашу реальность.</p>
          </article>
          <article className="card step-card card-lavender">
            <span className="step-no">02 / РЕПЕТИЦИЯ</span>
            <h3>Поговорите с AI</h3>
            <p className="soft">Говорите вслух, как в настоящем разговоре, а AI отвечает текстом — и учитесь реагировать в моменте.</p>
          </article>
          <article className="card step-card">
            <span className="step-no">03 / РАЗБОР</span>
            <h3>Унесите формулировки</h3>
            <p className="muted">Вердикт, слабые места и сильные альтернативы, которые можно применить завтра.</p>
          </article>
        </div>
      </section>

      <section className="section container-wide">
        <div className="split-section">
          <div className="section-heading">
            <span className="eyebrow">Почему не книга</span>
            <h2 className="display">Знание не помогает, пока не стало реакцией.</h2>
            <p className="muted">Можно понимать BATNA и всё равно теряться, когда собеседник давит. Мы тренируем не память, а спокойное действие.</p>
          </div>
          <div className="compare-list">
            <div className="compare-row"><div className="compare-cell">Книга рассказывает, как бывает</div><div className="compare-cell highlight">Fastur даёт попробовать</div></div>
            <div className="compare-row"><div className="compare-cell">Совет остаётся общим</div><div className="compare-cell highlight">Разбор привязан к вашей фразе</div></div>
            <div className="compare-row"><div className="compare-cell">Читаете в удобный момент</div><div className="compare-cell highlight">Репетируете под давлением</div></div>
            <div className="compare-row"><div className="compare-cell">Нет безопасного места для ошибки</div><div className="compare-cell highlight">Ошибка становится материалом</div></div>
          </div>
        </div>
      </section>

      <section className="section container-wide">
        <div className="section-heading">
          <span className="eyebrow">Маршруты</span>
          <h2 className="display">Ситуации, в которых нужен не скрипт, а опора.</h2>
        </div>
        <div className="category-grid">
          {categories.map(({ key, name, icon: Icon, description }) => (
            <article className="card category-card" key={key}>
              <div className="category-icon"><Icon size={18} /></div>
              <h3>{name}</h3>
              <p className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>{description}</p>
            </article>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section container-wide">
          <div className="section-heading">
            <span className="eyebrow">Попробуйте сейчас</span>
            <h2 className="display">Кейсы, которые звучат знакомо.</h2>
          </div>
          <div className="case-list">
            {featured.map((item) => (
              <div className="card" key={item.id}>
                <div
                  className="case-item"
                  onClick={() => setOpenCase(openCase === item.id ? null : item.id)}
                  role="button"
                  tabIndex={0}
                  data-testid={`button-case-${item.id}`}
                >
                  <div>
                    <span className="eyebrow">{categoryLabel(item.category)}</span>
                    <strong style={{ display: 'block', marginTop: 8 }}>{item.name}</strong>
                  </div>
                  <ChevronDown size={17} style={{ transform: openCase === item.id ? 'rotate(180deg)' : undefined, transition: '.2s' }} />
                </div>
                {openCase === item.id && (
                  <div className="case-detail">
                    {item.description || 'Описание появится после того, как вы откроете кейс.'}
                    <div style={{ marginTop: 14 }}>
                      <button className="btn btn-small btn-primary" onClick={() => openCaseInConstructor(item.id)}>
                        Открыть кейс <ArrowRight size={14} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="section container-wide">
        <div className="quote-grid">
          <div className="card quote card-lavender">
            <span className="eyebrow">Отзыв</span>
            <p>«Я впервые не репетировала идеальную речь. Я тренировала следующий вопрос — и это сработало.»</p>
            <small>Мария, руководитель продукта</small>
          </div>
          <div className="card quote">
            <span className="eyebrow">Отзыв</span>
            <p style={{ fontSize: 25 }}>«Разбор звучит как хороший коуч, а не как отчёт.»</p>
            <small>Илья, аккаунт-директор</small>
          </div>
        </div>
      </section>

      <section className="section container-wide">
        <div className="section-heading">
          <span className="eyebrow">Ответы</span>
          <h2 className="display">Вопросы перед первой тренировкой.</h2>
        </div>
        <div className="faq">
          {faqItems.map((item, i) => (
            <div className="card faq-item" key={item.q}>
              <button className="faq-button" onClick={() => setOpenFaq(openFaq === i ? null : i)} data-testid={`button-faq-${i}`}>
                {item.q}
                {openFaq === i ? <X size={17} /> : <ChevronDown size={17} />}
              </button>
              {openFaq === i && <div className="faq-answer">{item.a}</div>}
            </div>
          ))}
        </div>
      </section>

      <footer className="footer">
        <div className="container-wide" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
          <span><img src={logo} alt="Fastur" className="footer-logo" />Fastur · Speak Fastur</span>
          <span>Практика конфиденциальна</span>
        </div>
      </footer>
    </main>
  );
}
