import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function VerifyEmail() {
    const { token } = useParams();
    const [status, setStatus] = useState('verifying');
    const [message, setMessage] = useState('');
    const { verifyEmail } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const verify = async () => {
            try {
                const res = await verifyEmail(token);
                setStatus('success');
                setMessage(res.message);
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
            } catch (err) {
                setStatus('error');
                setMessage(err.message);
            }
        };
        verify();
    }, [token, verifyEmail, navigate]);

    return (
        <div className="min-h-screen bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
            <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-600/20 blur-[120px] pointer-events-none" />
            <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 glass-panel py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/5 text-center">
                
                {status === 'verifying' && (
                    <div className="flex flex-col items-center">
                        <Loader2 className="animate-spin h-12 w-12 text-emerald-500 mb-4" />
                        <h2 className="text-2xl font-bold text-white">Verifying Email...</h2>
                        <p className="text-gray-400 mt-2">Please wait while we verify your email address.</p>
                    </div>
                )}

                {status === 'success' && (
                    <div className="flex flex-col items-center">
                        <CheckCircle className="h-12 w-12 text-emerald-500 mb-4" />
                        <h2 className="text-2xl font-bold text-white">Verified!</h2>
                        <p className="text-emerald-400 mt-2">{message}</p>
                        <p className="text-gray-400 mt-4 text-sm">Redirecting to login...</p>
                    </div>
                )}

                {status === 'error' && (
                    <div className="flex flex-col items-center">
                        <XCircle className="h-12 w-12 text-red-500 mb-4" />
                        <h2 className="text-2xl font-bold text-white">Verification Failed</h2>
                        <p className="text-red-400 mt-2">{message}</p>
                        <div className="mt-6">
                            <Link to="/login" className="text-emerald-400 hover:underline">
                                Return to Login
                            </Link>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
