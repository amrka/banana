from unittest import TestCase
from nipype.interfaces.utility import IdentityInterface
from arcana.utils.testing import BaseTestCase
from banana.interfaces.mrtrix import MRConvert
from arcana.exceptions import ArcanaModulesNotInstalledException
from banana.file_format import (dicom_format, mrtrix_format,
                                    nifti_gz_format)
from arcana.study.base import Study, StudyMetaClass
from arcana.data import FilesetSelector, FilesetSpec, AcquiredFilesetSpec
from arcana.environment import ModulesEnvironment, StaticEnvironment

try:
    ModulesEnvironment._run_module_cmd('avail')
except ArcanaModulesNotInstalledException:
    environment = StaticEnvironment()
else:
    environment = ModulesEnvironment(fail_on_missing=False)


class DummyStudy(Study, metaclass=StudyMetaClass):

    add_data_specs = [
        AcquiredFilesetSpec('input_fileset', dicom_format),
        FilesetSpec('output_fileset', nifti_gz_format, 'a_pipeline')]

    def a_pipeline(self):
        pipeline = self.new_pipeline(
            name='a_pipeline',
            inputs=[FilesetSpec('input_fileset', nifti_gz_format)],
            outputs=[FilesetSpec('output_fileset', nifti_gz_format)],
            desc=("A dummy pipeline used to test dicom-to-nifti "
                         "conversion method"),
            references=[])
        identity = pipeline.create_node(IdentityInterface(['field']),
                                        name='identity')
        # Connect inputs
        pipeline.connect_input('input_fileset', identity, 'field')
        # Connect outputs
        pipeline.connect_output('output_fileset', identity, 'field')
        return pipeline


class TestConverterAvailability(TestCase):

    def test_find_mrtrix(self):
        converter = mrtrix_format.converter_from(dicom_format)
        self.assertIsInstance(converter.interface, MRConvert)


class TestDicom2Niix(BaseTestCase):

    def test_dcm2niix(self):
        study = self.create_study(
            DummyStudy,
            'concatenate',
            environment=environment,
            inputs=[
                FilesetSelector('input_fileset',
                                dicom_format, 't2_tse_tra_p2_448')])
        list(study.data('output_fileset'))[0]
        self.assertFilesetCreated('output_fileset.nii.gz', study.name)
