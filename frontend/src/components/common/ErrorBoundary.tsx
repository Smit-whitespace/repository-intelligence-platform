import { Component, type ErrorInfo, type ReactNode } from "react";
import { EmptyState } from "./EmptyState";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError() {
    return {
      hasError: true,
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E] p-8">
          <EmptyState
            title="Something went wrong"
            description="Refresh the page to restart the application shell."
          />
        </div>
      );
    }

    return this.props.children;
  }
}
