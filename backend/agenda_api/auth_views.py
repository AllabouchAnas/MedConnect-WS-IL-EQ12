from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from config.permissions import role_of

MAX_TENTATIVES = 5
BLOCAGE_SECONDES = 300


class LoginView(APIView):
    """Connexion JWT, blocage temporaire après 5 échecs (F001)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", ""))
        if not username or not password:
            return Response({"detail": "L'identifiant et le mot de passe sont obligatoires."}, status=400)
        key = f"login-fail:{username.lower()}"
        fails = cache.get(key, 0)
        if fails >= MAX_TENTATIVES:
            return Response({"detail": "Trop de tentatives. Réessayez dans quelques minutes."}, status=429)
        user = authenticate(request, username=username, password=password)
        if user is None:
            cache.set(key, fails + 1, BLOCAGE_SECONDES)
            return Response({"detail": "Identifiant ou mot de passe incorrect."}, status=401)
        cache.delete(key)
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token), "refresh": str(refresh),
            "user": {"username": user.username, "nom": user.get_full_name() or user.username,
                     "role": role_of(user)},
        })


class LogoutView(APIView):
    """Invalide le jeton de rafraîchissement (liste noire)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh", "")).blacklist()
        except TokenError:
            pass
        return Response({"detail": "Déconnecté."})
