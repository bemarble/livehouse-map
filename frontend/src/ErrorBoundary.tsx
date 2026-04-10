import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, color: "#c00" }}>
          <strong>エラーが発生しました</strong>
          <pre style={{ marginTop: 8, fontSize: 12 }}>{this.state.error.message}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
