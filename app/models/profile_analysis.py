from datetime import datetime
import json
from app import db


class ProfileAnalysis(db.Model):
    """Stores complete Trust Intelligence Reports for analysed social profiles."""
    __tablename__ = 'profile_analyses'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(100), nullable=False, index=True)
    display_name = db.Column(db.String(150), nullable=True)
    platform     = db.Column(db.String(50), default='Twitter/X')

    # Foreign key – links each analysis to the user who ran it
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )

    # ── Input Attributes ──────────────────────────────────────────────
    account_age_days          = db.Column(db.Integer,  default=0)
    followers_count           = db.Column(db.Integer,  default=0)
    following_count           = db.Column(db.Integer,  default=0)
    posts_count               = db.Column(db.Integer,  default=1)   # never 0
    has_profile_pic           = db.Column(db.Boolean,  default=True)
    has_bio                   = db.Column(db.Boolean,  default=True)
    is_verified               = db.Column(db.Boolean,  default=False)
    has_url                   = db.Column(db.Boolean,  default=False)
    avg_likes_per_post        = db.Column(db.Float,    default=0.0)
    avg_retweets_per_post     = db.Column(db.Float,    default=0.0)
    posting_frequency_per_day = db.Column(db.Float,    default=0.0)

    # ── Core AI Trust Metrics ─────────────────────────────────────────
    trust_score      = db.Column(db.Float,   nullable=False)
    confidence       = db.Column(db.Float,   nullable=False)
    risk_level       = db.Column(db.String(30),  nullable=False)
    recommendation   = db.Column(db.String(50),  nullable=False)
    health_meter     = db.Column(db.String(30),  nullable=False)
    behaviour_cluster = db.Column(db.String(50), nullable=False)
    digital_dna      = db.Column(db.String(20),  nullable=False)

    # ── JSON payloads ─────────────────────────────────────────────────
    sub_scores_json         = db.Column(db.Text, nullable=False, default='{}')
    trust_radar_json        = db.Column(db.Text, nullable=False, default='{}')
    timeline_json           = db.Column(db.Text, nullable=False, default='[]')
    heatmap_json            = db.Column(db.Text, nullable=False, default='{}')
    # Retained as shap_importance_json for backwards-compat with existing DBs
    shap_importance_json    = db.Column(db.Text, nullable=False, default='[]')
    ai_explanation_narrative = db.Column(db.Text, nullable=False, default='')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # ── Relationship back to User ─────────────────────────────────────
    # The backref 'analyses' is defined on the User model via the analyses relationship.

    # ── JSON properties ───────────────────────────────────────────────
    @property
    def sub_scores(self):
        return json.loads(self.sub_scores_json) if self.sub_scores_json else {}

    @sub_scores.setter
    def sub_scores(self, value):
        self.sub_scores_json = json.dumps(value)

    @property
    def trust_radar(self):
        return json.loads(self.trust_radar_json) if self.trust_radar_json else {}

    @trust_radar.setter
    def trust_radar(self, value):
        self.trust_radar_json = json.dumps(value)

    @property
    def timeline(self):
        return json.loads(self.timeline_json) if self.timeline_json else []

    @timeline.setter
    def timeline(self, value):
        self.timeline_json = json.dumps(value)

    @property
    def heatmap(self):
        return json.loads(self.heatmap_json) if self.heatmap_json else {}

    @heatmap.setter
    def heatmap(self, value):
        self.heatmap_json = json.dumps(value)

    @property
    def shap_importance(self):
        """Feature importance data (renamed from SHAP but kept as 'shap_importance' for template compat)."""
        return json.loads(self.shap_importance_json) if self.shap_importance_json else []

    @shap_importance.setter
    def shap_importance(self, value):
        self.shap_importance_json = json.dumps(value)

    def to_dict(self):
        """Serialise model for JSON APIs."""
        return {
            'id':             self.id,
            'username':       self.username,
            'display_name':   self.display_name,
            'platform':       self.platform,
            'user_id':        self.user_id,
            'trust_score':    self.trust_score,
            'confidence':     self.confidence,
            'risk_level':     self.risk_level,
            'recommendation': self.recommendation,
            'health_meter':   self.health_meter,
            'behaviour_cluster': self.behaviour_cluster,
            'digital_dna':    self.digital_dna,
            'sub_scores':     self.sub_scores,
            'trust_radar':    self.trust_radar,
            'timeline':       self.timeline,
            'heatmap':        self.heatmap,
            'feature_importance': self.shap_importance,
            'ai_explanation': self.ai_explanation_narrative,
            'created_at':     self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def __repr__(self):
        return (
            f'<ProfileAnalysis @{self.username} '
            f'(Score: {self.trust_score}, DNA: {self.digital_dna}, user_id: {self.user_id})>'
        )
