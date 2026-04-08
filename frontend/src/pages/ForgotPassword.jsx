import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Mail, ArrowRight, Loader2, KeyRound } from 'lucide-react';

export default function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const [message, setMessage] = useState('');
    const [demoToken, setDemoToken] = useState(null);

    const { requestPasswordReset } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('loading');
        try {
            const res = await requestPasswordReset(email);
            setStatus('success');
            setMessage(res.message);
            if (res.dev_reset_token) {
                setDemoToken(res.dev_reset_token);
            }
        } catch (err) {
            setStatus('error');
            setMessage(err.message);
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
            <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-violet-600/20 blur-[120px] pointer-events-none" />

            <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
                <div className="flex justify-center mb-4">
                    <KeyRound className="h-12 w-12 text-indigo-500" />
                </div>
                <h2 className="mt-6 text-center text-4xl font-black tracking-tight text-white">
                    Reset Password
                </h2>
                <p className="mt-2 text-center text-sm text-gray-400">
                    Enter your email to receive a reset link.
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
                <div className="glass-panel py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/5">
                    
                    {status === 'success' ? (
                        <div className="text-center space-y-4">
                            <div className="bg-emerald-500/10 border border-emerald-500/50 p-4 rounded-xl">
                                <p className="text-sm text-emerald-400 font-medium">{message}</p>
                            </div>
                            {demoToken && (
                                <div className="mt-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/50">
                                    <p className="text-xs text-indigo-300">
                                        [Demo Mode] Click <Link to={`/reset-password/${demoToken}`} className="underline font-bold text-indigo-400">here</Link> to simulate resetting your password.
                                    </p>
                                </div>
                            )}
                            <div className="mt-6">
                                <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition-colors">
                                    Return to Login
                                </Link>
                            </div>
                        </div>
                    ) : (
                        <form className="space-y-6" onSubmit={handleSubmit}>
                            {status === 'error' && (
                                <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl">
                                    <p className="text-sm text-red-400 text-center font-medium">{message}</p>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-gray-300">Email address</label>
                                <div className="mt-2 relative rounded-xl shadow-sm">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <Mail className="h-5 w-5 text-gray-500" />
                                    </div>
                                    <input
                                        type="email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="focus:ring-2 focus:ring-indigo-500 bg-gray-900 border border-gray-700 block w-full pl-10 sm:text-sm rounded-xl py-3 text-white transition-all outline-none placeholder-gray-500"
                                        placeholder="you@example.com"
                                    />
                                </div>
                            </div>

                            <div>
                                <button
                                    type="submit"
                                    disabled={status === 'loading'}
                                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-gray-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden"
                                >
                                    <span className="absolute w-0 h-0 transition-all duration-300 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-10"></span>
                                    <span className="relative flex items-center">
                                        {status === 'loading' ? (
                                            <><Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" /> Sending...</>
                                        ) : (
                                            <>Send Reset Link <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" /></>
                                        )}
                                    </span>
                                </button>
                            </div>
                            
                            <div className="text-center mt-4">
                                <Link to="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">
                                    Remember your password? Sign in
                                </Link>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
