from nianalysis.study.base import StudyMetaClass
from nianalysis.dataset import DatasetSpec, FieldSpec
from nianalysis.data_format import nifti_gz_format
from nianalysis.data_format import (text_matrix_format, directory_format,
                                     text_format, dicom_format)
from ..base import MRIStudy
from mbianalysis.citation import fsl_cite
from ..coregistered import CoregisteredStudy
from nianalysis.study.multi import (
    MultiStudy, SubStudySpec, MultiStudyMetaClass)
from mbianalysis.interfaces.custom.motion_correction import (
    MotionMatCalculation)
from nianalysis.option import OptionSpec


class T2Study(MRIStudy):

    __metaclass__ = StudyMetaClass

    add_option_specs = [
        OptionSpec('bet_robust', True),
        OptionSpec('bet_f_threshold', 0.5),
        OptionSpec('bet_reduce_bias', False)]

    def header_info_extraction_pipeline(self, **kwargs):
        return (super(T2Study, self).
                header_info_extraction_pipeline_factory(
                    'primary', **kwargs))


class CoregisteredT2Study(MultiStudy):

    __metaclass__ = MultiStudyMetaClass

    add_option_specs = [OptionSpec('resolution', [1]),
                        OptionSpec('multivol', False)]

    add_sub_study_specs = [
        SubStudySpec('t2', T2Study, {
            't2': 'primary',
            't2_nifti': 'primary_nifti',
            't2_preproc': 'preproc',
            't2_brain': 'masked',
            't2_brain_mask': 'brain_mask',
            'ped': 'ped',
            'pe_angle': 'pe_angle',
            'tr': 'tr',
            'real_duration': 'real_duration',
            'tot_duration': 'tot_duration',
            'start_time': 'start_time',
            'dcm_info': 'dcm_info'}),
        SubStudySpec('reference', MRIStudy, {
            'reference': 'primary_nifti',
            'ref_preproc': 'preproc',
            'ref_brain': 'masked',
            'ref_brain_mask': 'brain_mask'}),
        SubStudySpec('coreg', CoregisteredStudy, {
            't2_brain': 'to_register',
            'ref_brain': 'reference',
            't2_qformed': 'qformed',
            't2_qform_mat': 'qform_mat',
            't2_reg': 'registered',
            't2_reg_mat': 'matrix'})]

    add_data_specs = [
        DatasetSpec('t2', dicom_format),
        DatasetSpec('t2_nifti', nifti_gz_format, 't2_dcm2nii_pipeline'),
        DatasetSpec('reference', nifti_gz_format),
        DatasetSpec('t2_preproc', nifti_gz_format,
                    't2_basic_preproc_pipeline'),
        DatasetSpec('t2_brain', nifti_gz_format,
                    't2_brain_mask_pipeline'),
        DatasetSpec('t2_brain_mask', nifti_gz_format,
                    't2_brain_mask_pipeline'),
        DatasetSpec('ref_preproc', nifti_gz_format,
                    'ref_basic_preproc_pipeline'),
        DatasetSpec('t2_qformed', nifti_gz_format,
                    't2_qform_transform_pipeline'),
        DatasetSpec('masked', nifti_gz_format, 't2_bet_pipeline'),
        DatasetSpec('t2_qform_mat', text_matrix_format,
                    't2_qform_transform_pipeline'),
        DatasetSpec('ref_brain', nifti_gz_format, 'ref_bet_pipeline'),
        DatasetSpec('ref_brain_mask', nifti_gz_format,
                    'ref_bet_pipeline'),
        DatasetSpec('t2_reg', nifti_gz_format,
                    't2_rigid_registration_pipeline'),
        DatasetSpec('t2_reg_mat', text_matrix_format,
                    't2_rigid_registration_pipeline'),
        DatasetSpec('motion_mats', directory_format,
                    'motion_mat_pipeline'),
        DatasetSpec('dcm_info', text_format, 't2_dcm_info_pipeline'),
        FieldSpec('ped', str, 't2_dcm_info_pipeline'),
        FieldSpec('pe_angle', str, 't2_dcm_info_pipeline'),
        FieldSpec('tr', float, 't2_dcm_info_pipeline'),
        FieldSpec('start_time', str, 't2_dcm_info_pipeline'),
        FieldSpec('real_duration', str, 't2_dcm_info_pipeline'),
        FieldSpec('tot_duration', str, 't2_dcm_info_pipeline')]

    t2_basic_preproc_pipeline = MultiStudy.translate(
        't2', 'basic_preproc_pipeline')

    t2_dcm2nii_pipeline = MultiStudy.translate(
        't2', 'dcm2nii_conversion_pipeline')

    t2_dcm_info_pipeline = MultiStudy.translate(
        't2', 'header_info_extraction_pipeline')

    t2_bet_pipeline = MultiStudy.translate(
        't2', 'brain_mask_pipeline')

    ref_bet_pipeline = MultiStudy.translate(
        'reference', 'brain_mask_pipeline')

    ref_basic_preproc_pipeline = MultiStudy.translate(
        'reference', 'basic_preproc_pipeline')

    t2_qform_transform_pipeline = MultiStudy.translate(
        'coreg', 'qform_transform_pipeline')

    t2_brain_mask_pipeline = MultiStudy.translate(
        't2', 'brain_mask_pipeline')

    t2_rigid_registration_pipeline = MultiStudy.translate(
        'coreg', 'linear_registration_pipeline')

    def motion_mat_pipeline(self, **kwargs):

        pipeline = self.create_pipeline(
            name='motion_mat_calculation',
            inputs=[DatasetSpec('t2_reg_mat', text_matrix_format),
                    DatasetSpec('t2_qform_mat', text_matrix_format)],
            outputs=[DatasetSpec('motion_mats', directory_format)],
            description=("T2w Motion matrices calculation"),
            version=1,
            citations=[fsl_cite],
            **kwargs)

        mm = pipeline.create_node(
            MotionMatCalculation(), name='motion_mats')
        pipeline.connect_input('t2_reg_mat', mm, 'reg_mat')
        pipeline.connect_input('t2_qform_mat', mm, 'qform_mat')
        pipeline.connect_output('motion_mats', mm, 'motion_mats')
        return pipeline
