from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.video.models import VideoGenerationStep, VideoPart, VideoProject


class VideoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # VideoProject
    # ------------------------------------------------------------------

    async def create_project(self, project: VideoProject) -> VideoProject:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project_by_id(self, project_id: int) -> VideoProject | None:
        stmt = (
            select(VideoProject)
            .where(VideoProject.id == project_id)
            .options(
                selectinload(VideoProject.generation_steps),
                selectinload(VideoProject.parts),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_projects_by_user_id(self, user_id: int) -> list[VideoProject]:
        stmt = (
            select(VideoProject)
            .where(VideoProject.user_id == user_id)
            .order_by(VideoProject.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_project(self, project: VideoProject) -> VideoProject:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    # ------------------------------------------------------------------
    # VideoGenerationStep
    # ------------------------------------------------------------------

    async def create_step(self, step: VideoGenerationStep) -> VideoGenerationStep:
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def get_latest_step(self, project_id: int) -> VideoGenerationStep | None:
        stmt = (
            select(VideoGenerationStep)
            .where(VideoGenerationStep.project_id == project_id)
            .order_by(VideoGenerationStep.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_step_by_id(self, step_id: int) -> VideoGenerationStep | None:
        stmt = select(VideoGenerationStep).where(VideoGenerationStep.id == step_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_step(self, step: VideoGenerationStep) -> VideoGenerationStep:
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    # ------------------------------------------------------------------
    # VideoPart
    # ------------------------------------------------------------------

    async def create_video_part(self, part: VideoPart) -> VideoPart:
        self.db.add(part)
        await self.db.commit()
        await self.db.refresh(part)
        return part

    async def get_parts_by_project(self, project_id: int) -> list[VideoPart]:
        stmt = (
            select(VideoPart)
            .where(VideoPart.project_id == project_id)
            .order_by(VideoPart.part_number)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
