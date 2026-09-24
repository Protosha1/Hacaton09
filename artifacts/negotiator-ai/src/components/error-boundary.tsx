import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  resetKey?: unknown;
}

interface State {
  error: Error | null;
}

// Ловит ошибки рендера в дереве ниже и показывает понятный экран
// вместо белого пустого окна. resetKey (например, текущий route)
// позволяет сбросить состояние ошибки при переходе на другую страницу.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Необработанная ошибка в интерфейсе:', error, info.componentStack);
  }

  componentDidUpdate(prevProps: Props) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: '48px 20px', textAlign: 'center' }}>
          <h1 style={{ fontSize: 24, marginBottom: 12 }}>Что-то пошло не так</h1>
          <p style={{ color: '#a9a2c2', marginBottom: 20 }}>{this.state.error.message}</p>
          <button
            className="btn btn-primary"
            onClick={() => {
              this.setState({ error: null });
              window.location.href = '/';
            }}
          >
            На главную
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
