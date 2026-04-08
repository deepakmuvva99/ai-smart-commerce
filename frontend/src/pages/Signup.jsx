import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, ArrowRight, Loader2, User } from 'lucide-react';

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const { signup, loginWithGoogle, loginWithFacebook } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            return setError('Passwords do not match');
        }

        setIsLoading(true);
        try {
            const result = await signup(email, password);
            setSuccessMessage({
                message: result.message,
                token: result.verification_token
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-600/20 blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-600/20 blur-[120px] pointer-events-none" />

            <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
                <h2 className="mt-6 text-center text-4xl font-black tracking-tight text-white">
                    Join Smart Commerce.
                </h2>
                <p className="mt-2 text-center text-sm text-gray-400">
                    Already have an account?{' '}
                    <Link to="/login" className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
                        Sign in instead
                    </Link>
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
                <div className="glass-panel py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/5">
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {error && (
                            <div className="bg-red-500/10 border border-red-500/50 p-4 rounded-xl">
                                <p className="text-sm text-red-400 text-center font-medium">{error}</p>
                            </div>
                        )}
                        {successMessage && (
                            <div className="bg-emerald-500/10 border border-emerald-500/50 p-4 rounded-xl text-center">
                                <p className="text-sm text-emerald-400 font-medium">{successMessage.message}</p>
                                <p className="text-xs text-gray-400 mt-2">
                                    [Demo Mode] Click <Link to={`/verify/${successMessage.token}`} className="text-emerald-400 underline">here</Link> to simulate verifying your email.
                                </p>
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
                                    className="focus:ring-2 focus:ring-emerald-500 bg-gray-900 border border-gray-700 block w-full pl-10 sm:text-sm rounded-xl py-3 text-white transition-all outline-none placeholder-gray-500"
                                    placeholder="you@example.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300">Password</label>
                            <div className="mt-2 relative rounded-xl shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-500" />
                                </div>
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="focus:ring-2 focus:ring-emerald-500 bg-gray-900 border border-gray-700 block w-full pl-10 sm:text-sm rounded-xl py-3 text-white transition-all outline-none placeholder-gray-500"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300">Confirm Password</label>
                            <div className="mt-2 relative rounded-xl shadow-sm">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-500" />
                                </div>
                                <input
                                    type="password"
                                    required
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="focus:ring-2 focus:ring-emerald-500 bg-gray-900 border border-gray-700 block w-full pl-10 sm:text-sm rounded-xl py-3 text-white transition-all outline-none placeholder-gray-500"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-gray-900 bg-emerald-500 hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 focus:ring-offset-gray-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed group relative overflow-hidden"
                            >
                                <span className="absolute w-0 h-0 transition-all duration-300 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-20"></span>
                                <span className="relative flex items-center">
                                    {isLoading ? (
                                        <><Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" /> Creating Account...</>
                                    ) : (
                                        <>Create Account <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" /></>
                                    )}
                                </span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
