#!/usr/bin/env python
import os.path
from nipype import config
config.enable_debug_mode()
from arcana.data import FilesetSelector  # @IgnorePep8
from banana.study.mri.structural.diffusion import (  # @IgnorePep8
    DiffusionStudy, NODDIStudy)
from banana.file_format import (  # @IgnorePep8
    mrtrix_format, nifti_gz_format, fsl_bvals_format, fsl_bvecs_format,
    text_format)
from banana.testing import BaseTestCase, BaseMultiSubjectTestCase  # @IgnorePep8 @Reimport


class TestDiffusion(BaseTestCase):

    def test_preprocess(self):
        study = self.create_study(
            DiffusionStudy, 'preprocess', [
                FilesetSelector('magnitude', 'r_l_dwi_b700_30', mrtrix_format),
                FilesetSelector('dwi_reference', 'l_r_dwi_b0_6', mrtrix_format)])
        preproc = list(study.data('preproc'))[0]
        self.assertTrue(os.path.exists(preproc.path))

    def test_extract_b0(self):
        study = self.create_study(
            DiffusionStudy, 'extract_b0', [
                FilesetSelector('preproc', 'preproc', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradient_dirs', fsl_bvecs_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.extract_b0_pipeline().run(work_dir=self.work_dir)
        self.assertFilesetCreated('primary.nii.gz', study.name)

    def test_bias_correct(self):
        study = self.create_study(
            DiffusionStudy, 'bias_correct', [
                FilesetSelector('preproc', 'preproc', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradient_dirs', fsl_bvecs_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.bias_correct_pipeline(mask_tool='mrtrix').run(
            work_dir=self.work_dir)
        self.assertFilesetCreated('bias_correct.nii.gz', study.name)

    def test_tensor(self):
        study = self.create_study(
            DiffusionStudy, 'tensor', [
                FilesetSelector('bias_correct', 'bias_correct', nifti_gz_format),
                FilesetSelector('brain_mask', 'brain_mask', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradient_dirs', fsl_bvecs_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.tensor_pipeline().run(
            work_dir=self.work_dir)
        self.assertFilesetCreated('tensor.nii.gz', study.name)

    def test_response(self):
        study = self.create_study(
            DiffusionStudy, 'response', [
                FilesetSelector('bias_correct', 'bias_correct', nifti_gz_format),
                FilesetSelector('brain_mask', 'brain_mask', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradient_dirs', fsl_bvecs_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.response_pipeline().run(
            work_dir=self.work_dir)
        self.assertFilesetCreated('response.txt', study.name)

    def test_fod(self):
        study = self.create_study(
            DiffusionStudy, 'fod', [
                FilesetSelector('bias_correct', 'bias_correct', nifti_gz_format),
                FilesetSelector('brain_mask', 'brain_mask', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradient_dirs', fsl_bvecs_format),
                FilesetSelector('response', 'response', text_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.fod_pipeline().run(
            work_dir=self.work_dir)
        self.assertFilesetCreated('fod.mif', study.name)


class TestMultiSubjectDiffusion(BaseMultiSubjectTestCase):

    def test_intensity_normalization(self):
        study = self.create_study(
            DiffusionStudy, 'intens_norm', [
                FilesetSelector('bias_correct', 'biascorrect', nifti_gz_format),
                FilesetSelector('brain_mask', 'brainmask', nifti_gz_format),
                FilesetSelector('grad_dirs', 'gradientdirs', fsl_bvecs_format),
                FilesetSelector('bvalues', 'bvalues', fsl_bvals_format)])
        study.intensity_normalisation_pipeline().run(
            work_dir=self.work_dir)
        for subject_id in self.subject_ids:
            for visit_id in self.visit_ids(subject_id):
                self.assertFilesetCreated('norm_intensity.mif', study.name,
                                          subject=subject_id, visit=visit_id)
        self.assertFilesetCreated(
            'norm_intens_fa_template.mif', study.name,
            frequency='per_study')
        self.assertFilesetCreated(
            'norm_intens_wm_mask.mif', study.name,
            frequency='per_study')

    def test_average_response(self):
        study = self.create_study(
            DiffusionStudy, 'response', {
                FilesetSelector('response', 'response', text_format)})
        study.average_response_pipeline().run(work_dir=self.work_dir)
        for subject_id in self.subject_ids:
            for visit_id in self.visit_ids(subject_id):
                self.assertFilesetCreated('avg_response.txt', study.name,
                                          subject=subject_id, visit=visit_id)


class TestNODDI(BaseTestCase):

    def test_concatenate(self):
        study = self.create_study(
            NODDIStudy, 'concatenate', inputs=[
                FilesetSelector('low_b_dw_scan', 'r_l_dwi_b700_30', mrtrix_format),
                FilesetSelector('high_b_dw_scan', 'r_l_dwi_b2000_60', mrtrix_format)])
        study.concatenate_pipeline().run(work_dir=self.work_dir)
        self.assertFilesetCreated('dwi_scan.mif', study.name)
        # TODO: More thorough testing required

#     def test_noddi_fitting(self, nthreads=6):
#         study = self.create_study(
#             NODDIStudy, 'noddi', inputs=[
#                 FilesetSelector('preproc', 'noddi_dwi', mrtrix_format),
#                 FilesetSelector('brain_mask', 'roi_mask', analyze_format),
#                 'grad_dirs': Fileset('noddi_gradient_directions',
#                                      fsl_bvecs_format),
#                 FilesetSelector('bvalues', 'noddi_bvalues', fsl_bvals_format)})
#         study.noddi_fitting_pipeline(nthreads=nthreads).run(
#             work_dir=self.work_dir)
#         for out_name, mean, stdev in [('ficvf', 1e-5, 1e-2),
#                                       ('odi', 1e-4, 1e-2),
#                                       ('fiso', 1e-4, 1e-2),
#                                       ('fibredirs_xvec', 1e-3, 1e-1),
#                                       ('fibredirs_yvec', 1e-3, 1e-1),
#                                       ('fibredirs_zvec', 1e-3, 1e-1),
#                                       ('kappa', 1e-4, 1e-1)]:
#             self.assertImagesAlmostMatch(
#                 'example_{}.nii'.format(out_name), (out_name + '.nii'),
#                 mean_threshold=mean, stdev_threshold=stdev)
