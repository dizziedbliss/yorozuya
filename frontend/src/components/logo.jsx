export default function Logo({ className }) {
    return (
        <div className={`logo-container ${className}`}>
            <div className="logo font-heading font-black text-9xl text-center tracking-tighter -mb-2">
                <h1>Yorozuya</h1>
            </div>

            <div className="sub text-center text-accent font-heading -translate-y-21 text-2xl tracking-wide">
                House of 1000 jobs
            </div>

        </div>
    );
}