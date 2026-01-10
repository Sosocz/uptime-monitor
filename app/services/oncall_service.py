"""
On-Call Service
Handles on-call schedule management and shift calculations.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.oncall import OnCallSchedule, OnCallShift, RotationType


class OnCallService:
    """Service for managing on-call schedules and shifts."""

    @staticmethod
    def get_current_oncall_user(schedule_id: int, db: Session, current_time: Optional[datetime] = None) -> Optional[int]:
        """
        Get the user ID who is currently on-call for a given schedule.

        Args:
            schedule_id: ID of the on-call schedule
            db: Database session
            current_time: Optional time to check (defaults to now)

        Returns:
            User ID if someone is on-call, None otherwise
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Find active shift that covers current time
        shift = db.query(OnCallShift).filter(
            and_(
                OnCallShift.schedule_id == schedule_id,
                OnCallShift.start_time <= current_time,
                OnCallShift.end_time >= current_time,
                OnCallShift.is_active == True
            )
        ).order_by(
            OnCallShift.is_override.desc(),  # Overrides take priority
            OnCallShift.start_time.desc()
        ).first()

        return shift.user_id if shift else None

    @staticmethod
    def get_all_oncall_users(db: Session, current_time: Optional[datetime] = None) -> List[dict]:
        """
        Get all currently on-call users across all active schedules.

        Args:
            db: Database session
            current_time: Optional time to check (defaults to now)

        Returns:
            List of dicts with schedule info and user ID
        """
        if current_time is None:
            current_time = datetime.utcnow()

        active_schedules = db.query(OnCallSchedule).filter(
            OnCallSchedule.is_active == True
        ).all()

        result = []
        for schedule in active_schedules:
            user_id = OnCallService.get_current_oncall_user(schedule.id, db, current_time)
            if user_id:
                result.append({
                    "schedule_id": schedule.id,
                    "schedule_name": schedule.name,
                    "user_id": user_id,
                    "timezone": schedule.timezone
                })

        return result

    @staticmethod
    def create_override_shift(
        schedule_id: int,
        original_shift_id: int,
        override_user_id: int,
        overridden_by_id: int,
        reason: Optional[str],
        db: Session
    ) -> OnCallShift:
        """
        Create an override shift to replace an existing shift.

        Args:
            schedule_id: Schedule ID
            original_shift_id: Shift to override
            override_user_id: User taking over the shift
            overridden_by_id: User creating the override
            reason: Reason for override
            db: Database session

        Returns:
            The created override shift
        """
        original_shift = db.query(OnCallShift).filter(
            OnCallShift.id == original_shift_id
        ).first()

        if not original_shift:
            raise ValueError("Original shift not found")

        # Deactivate original shift
        original_shift.is_active = False

        # Create override shift
        override_shift = OnCallShift(
            schedule_id=schedule_id,
            user_id=override_user_id,
            start_time=original_shift.start_time,
            end_time=original_shift.end_time,
            is_override=True,
            overridden_shift_id=original_shift_id,
            override_reason=reason,
            overridden_by_id=overridden_by_id,
            is_active=True
        )

        db.add(override_shift)
        db.commit()
        db.refresh(override_shift)

        return override_shift

    @staticmethod
    def generate_rotation_shifts(
        schedule: OnCallSchedule,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> List[OnCallShift]:
        """
        Generate shifts for a rotation schedule within a date range.

        Args:
            schedule: On-call schedule
            start_date: Start of period to generate shifts
            end_date: End of period to generate shifts
            db: Database session

        Returns:
            List of created shifts
        """
        shifts = []
        current_start = max(start_date, schedule.rotation_start)
        user_index = 0

        while current_start < end_date:
            # Calculate shift end based on rotation interval
            shift_end = current_start + timedelta(hours=schedule.rotation_interval_hours)

            # Don't exceed end_date
            if shift_end > end_date:
                shift_end = end_date

            # Get user for this rotation
            user_ids = schedule.rotation_user_ids
            if not user_ids or len(user_ids) == 0:
                break

            user_id = user_ids[user_index % len(user_ids)]

            # Create shift
            shift = OnCallShift(
                schedule_id=schedule.id,
                user_id=user_id,
                start_time=current_start,
                end_time=shift_end,
                is_override=False,
                is_active=True
            )

            db.add(shift)
            shifts.append(shift)

            # Move to next rotation
            current_start = shift_end
            user_index += 1

        db.commit()
        return shifts

    @staticmethod
    def get_upcoming_shifts(schedule_id: int, days: int, db: Session) -> List[OnCallShift]:
        """
        Get upcoming shifts for a schedule.

        Args:
            schedule_id: Schedule ID
            days: Number of days to look ahead
            db: Database session

        Returns:
            List of upcoming shifts
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        shifts = db.query(OnCallShift).filter(
            and_(
                OnCallShift.schedule_id == schedule_id,
                OnCallShift.start_time >= now,
                OnCallShift.start_time <= end_date,
                OnCallShift.is_active == True
            )
        ).order_by(OnCallShift.start_time).all()

        return shifts
