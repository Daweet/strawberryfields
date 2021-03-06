##############################################################################
#
# Unit tests for the loss channel
# Convention: The loss channel N(T) has the action
# N(T){|n><m|} = \sum_{l=0}^{min(m,n)} ((1-T)/T) ^ l * T^((n+m)/2) / l! * \sqrt(n!m!/((n-l)!(m-l)!))n-l><m-l|
#
##############################################################################

import unittest

import numpy as np
from scipy.special import factorial

from defaults import BaseTest, GaussianBaseTest, FockBaseTest


loss_Ts = np.linspace(0., 1., 3, endpoint=True)
mag_alphas = np.linspace(0, .75, 3)
phase_alphas = np.linspace(0, 2 * np.pi, 3, endpoint=False)

###################################################################


class BasicTests(BaseTest):
    """Basic implementation-independent tests."""
    num_subsystems = 1

    def test_loss_channel_on_vacuum(self):
        """Tests loss channels on vacuum (result should be vacuum)."""
        self.logTestName()
        for T in loss_Ts:
            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.loss(T, 0)
            self.assertAllTrue(self.circuit.is_vacuum(self.tol))

    def test_full_loss_channel_on_coherent_states(self):
        """Tests the full-loss channel on various states (result should be vacuum)."""
        self.logTestName()
        T = 0.0
        for mag_alpha in mag_alphas:
            for phase_alpha in phase_alphas:
                alpha = mag_alpha * np.exp(1j * phase_alpha)
                self.circuit.reset(pure=self.kwargs['pure'])
                self.circuit.displacement(alpha, 0)
                self.circuit.loss(T, 0)
                self.assertAllTrue(self.circuit.is_vacuum(self.tol))
                if alpha == 0.:
                    break


class GaussianBasisTests(GaussianBaseTest):
    """Tests for the thermal loss channel (currently only
    supported by the Gaussian backend"""
    num_subsystems = 1

    def test_thermal_loss_channel_with_vacuum(self):
        """Tests thermal loss channel with nbar=0 (should be same as loss channel)."""
        self.logTestName()
        z = 0.432*np.exp(1j*0.534)
        alpha = 0.654 + 1j*0.239
        nbar = 0.
        for T in loss_Ts:
            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.squeeze(z, 0)
            self.circuit.displacement(alpha, 0)
            self.circuit.loss(T, 0)
            state1 = self.circuit.state()

            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.squeeze(z, 0)
            self.circuit.displacement(alpha, 0)
            self.circuit.thermal_loss(T, nbar, 0)
            state2 = self.circuit.state()

            self.assertAllAlmostEqual(state1.means(), state2.means(), delta=self.tol)
            self.assertAllAlmostEqual(state1.cov(), state2.cov(), delta=self.tol)

    def test_full_thermal_loss_channel(self):
        """Tests thermal loss channel with T=0 (should produce a thermal state)."""
        self.logTestName()
        z = 0.432*np.exp(1j*0.534)
        alpha = 0.654 + 1j*0.239
        T = 0
        for nbar in mag_alphas:
            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.prepare_thermal_state(nbar, 0)
            state1 = self.circuit.state()

            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.squeeze(z, 0)
            self.circuit.displacement(alpha, 0)
            self.circuit.thermal_loss(T, nbar, 0)
            state2 = self.circuit.state()

            self.assertAllAlmostEqual(state1.means(), state2.means(), delta=self.tol)
            self.assertAllAlmostEqual(state1.cov(), state2.cov(), delta=self.tol)

    def test_thermal_loss_channel_on_squeezed_state(self):
        """Tests thermal loss channel on a squeezed state"""
        self.logTestName()
        r = 0.432
        for T in loss_Ts:
            for nbar in mag_alphas:
                self.circuit.reset(pure=self.kwargs['pure'])
                self.circuit.squeeze(r, 0)
                self.circuit.thermal_loss(T, nbar, 0)
                state = self.circuit.state()

                res = state.cov()
                exp = np.diag([T*np.exp(-2*r) + (1-T)*(2*nbar+1),
                               T*np.exp(2*r) + (1-T)*(2*nbar+1)])

                self.assertAllAlmostEqual(res, exp, delta=self.tol)


class FockBasisTests(FockBaseTest):
    """Tests for simulators that use Fock basis."""
    num_subsystems = 1

    def test_normalized_after_loss_channel_on_coherent_state(self):
        """Tests if a range of loss states are normalized."""
        self.logTestName()
        for T in loss_Ts:
            for mag_alpha in mag_alphas:
                for phase_alpha in phase_alphas:
                    alpha = mag_alpha * np.exp(1j * phase_alpha)
                    self.circuit.reset(pure=self.kwargs['pure'])
                    self.circuit.prepare_coherent_state(alpha, 0)
                    self.circuit.loss(T, 0)
                    state = self.circuit.state()
                    tr = state.trace()
                    self.assertAllAlmostEqual(tr, 1, delta=self.tol)

    def test_normalized_after_loss_channel_on_fock_state(self):
        """Tests if a range of loss states are normalized."""
        self.logTestName()
        for T in loss_Ts:
            for n in range(self.D):
                self.circuit.reset(pure=self.kwargs['pure'])
                self.circuit.prepare_fock_state(n, 0)
                self.circuit.loss(T, 0)
                state = self.circuit.state()
                tr = state.trace()
                self.assertAllAlmostEqual(tr, 1, delta=self.tol)

    def test_full_loss_channel_on_fock_states(self):
        """Tests the full-loss channel on various states (result should be vacuum)."""
        self.logTestName()
        T = 0.0
        for n in range(self.D):
            self.circuit.reset(pure=self.kwargs['pure'])
            self.circuit.prepare_fock_state(n, 0)
            self.circuit.loss(T, 0)
            self.assertAllTrue(self.circuit.is_vacuum(self.tol))

    def test_loss_channel_on_coherent_states(self):
        """Tests various loss channels on coherent states (result should be coherent state with amplitude weighted by \sqrt(T)."""
        self.logTestName()
        for T in loss_Ts:
            for mag_alpha in mag_alphas:
                for phase_alpha in phase_alphas:
                    alpha = mag_alpha * np.exp(1j * phase_alpha)
                    rootT_alpha = np.sqrt(T) * alpha
                    self.circuit.reset(pure=self.kwargs['pure'])
                    self.circuit.prepare_coherent_state(alpha, 0)
                    self.circuit.loss(T, 0)
                    s = self.circuit.state()
                    if s.is_pure:
                        numer_state = s.ket()
                    else:
                        numer_state = s.dm()
                    ref_state = np.array([np.exp(-0.5 * np.abs(rootT_alpha) ** 2) * rootT_alpha ** n / np.sqrt(factorial(n)) for n in range(self.D)])
                    ref_state = np.outer(ref_state, np.conj(ref_state))
                    self.assertAllAlmostEqual(numer_state, ref_state, delta=self.tol)
                    if alpha == 0.:
                        break


if __name__=="__main__":
    # run the tests in this file
    suite = unittest.TestSuite()
    for t in (BasicTests, GaussianBasisTests, FockBasisTests):
        ttt = unittest.TestLoader().loadTestsFromTestCase(t)
        suite.addTests(ttt)

    unittest.TextTestRunner().run(suite)
